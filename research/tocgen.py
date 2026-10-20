import fitz, json, re
heads = json.load(open('headings.json')); caps = json.load(open('caps.json'))
d = fitz.open('MST_Clustering_Mini_Project_Report.pdf')
def lines(i): return [l.strip() for l in d[i].get_text().split('\n')]
def roman(n):
    o=''
    for v,s in [(10,'x'),(9,'ix'),(5,'v'),(4,'iv'),(1,'i')]:
        while n>=v: o+=s; n-=v
    return o
# locate pages
front = {}
titles = {'Acknowledgement':'Acknowledgement','Declaration':'DECLARATION','Certificate':'Certificate',
          'Table of Contents':'TABLE OF CONTENTS','List of Figures':'LIST OF FIGURES','List of Tables':'LIST OF TABLES','Abstract':'ABSTRACT'}
for k, t in titles.items():
    for i in range(1, len(d)):
        if t in lines(i)[:6]: front[k] = i; break
first_main = None
for i in range(front['Abstract']+1, len(d)):
    if 'CHAPTER 1' in lines(i): first_main = i; break
def disp(i): return roman(i) if i < first_main else str(i - first_main + 1)
out = {}
for k, i in front.items(): out['front:'+k] = roman(i)   # roman: pdf page 1 is cover -> i = pdf idx
for h in heads:
    if h['level'] == 0: continue
    s = h['search']
    for i in range(first_main, len(d)):
        L = lines(i)
        if h['level'] == 1 and s.startswith('CHAPTER'):
            ok = s in L
        else:
            ok = any(l.startswith(s[:45]) for l in L)
        if ok: out[h['key']] = disp(i); break
    else: print('MISSING', h['key'])
for c in caps:
    pref = c['label'] + ':'
    for i in range(first_main, len(d)):
        if any(l.startswith(pref) for l in lines(i)): out['cap:'+c['label']] = disp(i); break
    else: print('MISSING cap', c['label'])
json.dump(out, open('toc_pages.json','w'), indent=0); print(len(out), 'entries; main starts pdf idx', first_main)
