#!/usr/bin/env python3
"""Trace the approved Peyvand raster into an editable, font-free SVG master.

The source image is never modified. Marching squares measures the subpixel
boundary halfway between the foreground/background luminance. Cubic Bézier
fitting compresses that measured outline while retaining sharp terminals.
Dependencies: the project's numpy, scipy and cv2; rsvg-convert for validation.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/branding/peyvand-logo.png"
OUT = ROOT / "assets/branding/master"
TOLERANCE = 0.65
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def unit(vector):
    length = np.linalg.norm(vector)
    return vector / length if length > 1e-12 else np.array([1.0, 0.0])


def marching_contours(gray, level):
    """Return closed analytical isocontours in SVG pixel-center coordinates."""
    a, b = gray[:-1, :-1], gray[:-1, 1:]
    c, d = gray[1:, 1:], gray[1:, :-1]
    low = np.minimum(np.minimum(a, b), np.minimum(c, d))
    high = np.maximum(np.maximum(a, b), np.maximum(c, d))
    ys, xs = np.where((low < level) & (high >= level))
    coordinates, adjacency = {}, {}
    for y, x in zip(ys, xs):
        values = [gray[y, x], gray[y, x + 1], gray[y + 1, x + 1], gray[y + 1, x]]
        positions = [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]
        keys = [(0, y, x), (1, y, x + 1), (0, y + 1, x), (1, y, x)]
        crossings = []
        for i, j in [(0, 1), (1, 2), (2, 3), (3, 0)]:
            if (values[i] < level) != (values[j] < level):
                key = keys[i]
                t = (level - values[i]) / (values[j] - values[i])
                coordinates[key] = np.array(positions[i]) + t * (np.array(positions[j]) - positions[i]) + 0.5
                crossings.append(key)
        if len(crossings) == 4:
            # Asymptotic decider for a rare saddle pixel.
            if (np.mean(values) < level) != (values[0] < level):
                pairs = [(crossings[0], crossings[3]), (crossings[1], crossings[2])]
            else:
                pairs = [(crossings[0], crossings[1]), (crossings[2], crossings[3])]
        else:
            pairs = [(crossings[0], crossings[1])]
        for p, q in pairs:
            adjacency.setdefault(p, []).append(q)
            adjacency.setdefault(q, []).append(p)
    unvisited = set(adjacency)
    contours = []
    while unvisited:
        start = min(unvisited)
        current, previous, points = start, None, []
        while True:
            points.append(coordinates[current])
            unvisited.discard(current)
            following = next(p for p in adjacency[current] if p != previous)
            previous, current = current, following
            if current == start:
                break
        if len(points) > 12:
            contours.append(np.asarray(points))
    return contours


def bezier(curve, u):
    u = np.asarray(u)
    return ((1-u)**3)[..., None] * curve[0] + (3*u*(1-u)**2)[..., None] * curve[1] + (3*u*u*(1-u))[..., None] * curve[2] + (u**3)[..., None] * curve[3]


def generate_curve(points, u, left, right):
    b0, b1, b2, b3 = (1-u)**3, 3*u*(1-u)**2, 3*u*u*(1-u), u**3
    a1, a2 = b1[:, None] * left, b2[:, None] * right
    residual = points - (b0+b1)[:, None]*points[0] - (b2+b3)[:, None]*points[-1]
    matrix = np.array([[np.sum(a1*a1), np.sum(a1*a2)], [np.sum(a1*a2), np.sum(a2*a2)]])
    rhs = np.array([np.sum(a1*residual), np.sum(a2*residual)])
    alpha = np.linalg.lstsq(matrix, rhs, rcond=None)[0]
    distance = np.linalg.norm(points[-1]-points[0])
    if np.min(alpha) < 1e-6*distance or np.max(alpha) > 2*np.sum(np.linalg.norm(np.diff(points,axis=0),axis=1)):
        alpha[:] = distance/3
    return np.array([points[0], points[0]+left*alpha[0], points[-1]+right*alpha[1], points[-1]])


def fit_curve(points, left, right, tolerance=TOLERANCE):
    if len(points) == 2:
        distance = np.linalg.norm(points[1]-points[0])/3
        return [np.array([points[0], points[0]+left*distance, points[1]+right*distance, points[1]])]
    u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    u /= u[-1]
    for iteration in range(5):
        curve = generate_curve(points, u, left, right)
        errors = np.sum((bezier(curve, u)-points)**2, axis=1)
        split = int(np.argmax(errors))
        if errors[split] < tolerance*tolerance:
            return [curve]
        if iteration == 4 or errors[split] > 16*tolerance*tolerance:
            break
        q = bezier(curve, u)
        first = 3*((1-u)**2)[:,None]*(curve[1]-curve[0]) + 6*(u*(1-u))[:,None]*(curve[2]-curve[1]) + 3*(u*u)[:,None]*(curve[3]-curve[2])
        second = 6*(1-u)[:,None]*(curve[2]-2*curve[1]+curve[0]) + 6*u[:,None]*(curve[3]-2*curve[2]+curve[1])
        numerator = np.sum((q-points)*first,axis=1)
        denominator = np.sum(first*first+(q-points)*second,axis=1)
        updated = np.clip(u-numerator/np.where(np.abs(denominator)>1e-12,denominator,1),0,1)
        if np.any(np.diff(updated)<0):
            break
        u=updated
    split = min(max(split,1),len(points)-2)
    center=unit(points[split-1]-points[split+1])
    return fit_curve(points[:split+1],left,center,tolerance)+fit_curve(points[split:],-center,right,tolerance)


def trace_contour(points, anchors=()):
    """Fit curves between corners; cornerless loops get smooth quarter splits."""
    n=len(points)
    if anchors:
        breaks = sorted(set(int(np.argmin(np.sum((points-anchor)**2,axis=1))) for anchor in anchors))
        corners=set(breaks)
    else:
        polygon=cv2.approxPolyDP(points.astype(np.float32), 1.4, True).reshape(-1,2)
        corners=set()
        for i,p in enumerate(polygon):
            incoming=unit(p-polygon[i-1]); outgoing=unit(polygon[(i+1)%len(polygon)]-p)
            if np.dot(incoming,outgoing)<np.cos(np.radians(43)):
                # Tiny round dots are smooth even if their polygon is angular.
                if np.ptp(points[:,0])>60 or np.ptp(points[:,1])>60:
                    corners.add(int(np.argmin(np.sum((points-p)**2,axis=1))))
        breaks=sorted(corners) if corners else [0,n//4,n//2,3*n//4]
    curves=[]
    for i,start in enumerate(breaks):
        end=breaks[(i+1)%len(breaks)]
        indexes=np.arange(start,end+n+1 if end<=start else end+1)%n
        segment=points[indexes]
        if start in corners:
            left=unit(segment[min(5,len(segment)-1)]-segment[0])
        else:
            left=unit(points[(start+4)%n]-points[(start-4)%n])
        if end in corners:
            right=unit(segment[max(0,len(segment)-6)]-segment[-1])
        else:
            right=unit(points[(end-4)%n]-points[(end+4)%n])
        curves.extend(fit_curve(segment,left,right))
    fmt=lambda p: f"{p[0]:.3f},{p[1]:.3f}"
    path=f"M {fmt(curves[0][0])} "
    for curve in curves:
        # True straight runs retain editable line segments.
        chord=curve[-1]-curve[0]
        distance=np.abs((chord[0]*(curve[1:3,1]-curve[0,1])-chord[1]*(curve[1:3,0]-curve[0,0])))/max(np.linalg.norm(chord),1e-12)
        if np.max(distance)<0.15:
            path+=f"L {fmt(curve[3])} "
        else:
            path+=f"C {fmt(curve[1])} {fmt(curve[2])} {fmt(curve[3])} "
    return path+"Z",len(curves)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    image=cv2.imread(str(SOURCE))
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY).astype(float)
    foreground=np.median(gray[gray<50]); background=np.median(gray[gray>200])
    level=(foreground+background)/2
    contours=marching_contours(gray,level)
    contours.sort(key=lambda points: -abs(cv2.contourArea(points.astype(np.float32))))
    height,width=gray.shape
    svg=ET.Element(f"{{{SVG_NS}}}svg",{"width":str(width),"height":str(height),"viewBox":f"0 0 {width} {height}","fill":"#15181B","role":"img","aria-labelledby":"logo-title logo-description"})
    ET.SubElement(svg,f"{{{SVG_NS}}}title",{"id":"logo-title"}).text="پیوند — Peyvand"
    ET.SubElement(svg,f"{{{SVG_NS}}}desc",{"id":"logo-description"}).text="Editable vector trace of the approved abstract exchange mark and original Persian wordmark. The left stroke, right stroke, and complete wordmark are separate animation groups. Transparent background."
    ET.SubElement(svg,f"{{{SVG_NS}}}metadata").text=json.dumps({"source":"../peyvand-logo.png","method":"Measured raster isocontours fitted to cubic Bézier paths; no font substitution","source_size":[width,height],"foreground":"#15181B","reference_background":"#E9ECEF","curve_fit_tolerance_px":TOLERANCE},ensure_ascii=False)
    groups={name:ET.SubElement(svg,f"{{{SVG_NS}}}g",{"id":name}) for name in ["stroke-left","stroke-right","wordmark"]}
    summary=[]
    for i,points in enumerate(contours):
        minimum=points.min(axis=0); maximum=points.max(axis=0)
        if maximum[1]<1100:
            if minimum[0]<200:
                group="stroke-left"; anchors=[(641,84),(641,291),(197,857)]
            else:
                group="stroke-right"; anchors=[(988,419),(776,543),(424,1058)]
        else:
            group="wordmark"; anchors=[]
        d,segments=trace_contour(points,anchors)
        path=ET.SubElement(groups[group],f"{{{SVG_NS}}}path",{"id":f"outline-{i+1}","d":d})
        summary.append({"id":path.attrib["id"],"group":group,"segments":segments,"bounds":[*minimum.tolist(),*maximum.tolist()]})
    # The only counter is the small hollow within و. Merge it into the body
    # using evenodd fill so that transparency and inversion both work.
    wordmark=groups['wordmark']
    for item in list(wordmark):
        info=next(row for row in summary if row['id']==item.attrib['id'])
        x0,y0,x1,y1=info['bounds']
        if 525<x0<535 and 1218<y0<1230 and x1<570 and y1<1250:
            body=next(node for node in wordmark if node.attrib['id']==next(row['id'] for row in summary if row['group']=='wordmark' and row['bounds'][0]<500 and row['bounds'][2]>800))
            body.attrib['d']+=' '+item.attrib['d']
            body.attrib['fill-rule']='evenodd'
            wordmark.remove(item)
            info['merged_into']=body.attrib['id']
    target=OUT/'peyvand-logo-master.svg'
    ET.indent(svg,space="  ")
    ET.ElementTree(svg).write(target,encoding="utf-8",xml_declaration=True)
    preview=OUT/'peyvand-logo-master-validation.png'
    subprocess.run(['rsvg-convert',str(target),'-o',str(preview)],check=True)
    rendered=cv2.imread(str(preview),cv2.IMREAD_UNCHANGED)
    reference=gray<level; vector=rendered[:,:,3]>=128
    intersection=np.count_nonzero(reference&vector); union=np.count_nonzero(reference|vector)
    contours_ref,_=cv2.findContours(reference.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    contours_vec,_=cv2.findContours(vector.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    from scipy.spatial import cKDTree
    ref_points=np.concatenate(contours_ref).reshape(-1,2); vec_points=np.concatenate(contours_vec).reshape(-1,2)
    distances=np.r_[cKDTree(ref_points).query(vec_points)[0],cKDTree(vec_points).query(ref_points)[0]]
    alpha=rendered[:,:,3].astype(float)/255
    # Estimate antialiased source opacity only for a fidelity metric, not export.
    source_alpha=np.clip((background-gray)/(background-foreground),0,1)
    report={"source":str(SOURCE.relative_to(ROOT)),"master":str(target.relative_to(ROOT)),"canvas_px":[width,height],"palette":{"foreground":"#15181B","reference_background":"#E9ECEF"},"threshold_luminance":level,"fit_tolerance_px":TOLERANCE,"groups":["stroke-left","stroke-right","wordmark"],"path_count":len(svg.findall('.//{'+SVG_NS+'}path')),"bezier_or_line_segments":sum(row['segments'] for row in summary),"foreground_mask_iou":intersection/union,"differing_binary_pixels":int(np.count_nonzero(reference^vector)),"boundary_max_deviation_px":float(distances.max()),"boundary_p95_deviation_px":float(np.percentile(distances,95)),"boundary_mean_deviation_px":float(distances.mean()),"source_opacity_mean_absolute_error":float(np.mean(np.abs(alpha-source_alpha))),"all_paths_closed":True,"contains_embedded_images":False,"contains_fonts_or_text_elements":False,"contours":summary}
    (OUT/'geometry-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:value for key,value in report.items() if key!='contours'},indent=2))


if __name__=='__main__':
    main()
