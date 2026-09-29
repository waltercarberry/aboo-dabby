#!/usr/bin/env python3
"""
ADIO positioning analysis.

Reads a search-results JSON (keys: "web" with title/description, "news" with title/snippet),
runs keyword-frequency and ADIO-positioning analysis, and writes:
  - adio_positioning.html  (quadrant + heatmap + keyword bars + ADIO table)
  - analysis_data.json     (all numbers behind the charts)

Usage:
  python analyze_adio.py abu_dhabi_investment_results.json
  python analyze_adio.py input.json --out-dir output
"""
import argparse, json, re, collections, os

ap = argparse.ArgumentParser()
ap.add_argument("input", help="path to the search-results JSON")
ap.add_argument("--out-dir", default=".", help="where to write the outputs")
args = ap.parse_args()
IN_PATH = args.input
os.makedirs(args.out_dir, exist_ok=True)

# ---------------------------------------------------------------- 1. LOAD
# Web rows use "description" as their snippet; news rows use "snippet".
d=json.load(open(IN_PATH))
rows=[dict(src='web',title=x['title'],text=x['description'] or '',url=x['url']) for x in d['web']]+[dict(src='news',title=x['title'],text=x['snippet'] or '',url=x['url']) for x in d['news']]
for k,r in enumerate(rows): r['i']=k
# ---------------------------------------------------------------- 2. CLEAN
# Only the first CAP characters of each snippet are scanned for sector terms, so one
# very long page (e.g. a 10k-character interview) cannot dominate the counts.
CAP=6000
seen=set();uniq=[]
for r in rows:
    key=re.sub(r'\W+','',r['title'].lower())[:60]
    if key in seen: continue
    seen.add(key);uniq.append(r)
# Off-topic screen: encyclopaedia entries, unrelated market reports, travel/listings.
OFF=r"wikipedia|market (size|analysis|report)[^|]*20(2[7-9]|3\d)|forecast to 20|flights|book fair|concerts|cost of living|metro guide|sleeping pods|cruise|yacht|leather|elevator market|outdoor lighting|medical aesthetics|3d metrology|paints and coatings|petites annonces|nicaragua newswire|press center, distribute|ktoo|jordan news|mail & guardian|travel daily|eegaming|michelin|museums to explore|things to do|recruitment agency|bni winner|instagram\.com/reel|iran in brics|heritage status|freelander|south denes|britannica|homepage|middle east news 247|dubai metro"
off=re.compile(OFF,re.I)
for r in uniq:
    r['text']=re.sub(r'(?m)^\s*- \[[^\n]*$','',r['text'])
    r['full']=(r['title']+' . '+r['text']).lower()
    r['blob']=(r['title']+' . '+r['text'][:CAP]).lower()
    r['off']=bool(off.search(r['title']+' '+r['url']))
# keep Sukuk wiki off too
on=[r for r in uniq if not r['off']]
print('raw',len(rows),'unique',len(uniq),'on-topic',len(on))
# ---------------------------------------------------------------- 3. TAG
# Sector lenses (keyword regexes). Edit these to change what counts as a sector.
SECT={
 'Financial services & capital':r'fintech|financ|bank|capital market|asset manage|assets under|\bfund\b|funds\b|sukuk|private equity|hedge|insur|reinsur|retirement|wealth|family office|sovereign|adgm|\baum\b|investor',
 'AI & digital tech':r'\bai\b|artificial intelligence|data cent|digital|(?<!bio)technolog|semiconductor|robotic|cyber|\bmgx\b|software',
 'Advanced manufacturing & industry':r'manufactur|industrial|factory|factories|production|supply chain|localis|import substitution|fabrication',
 'Automotive & mobility':r'automotive|\bcar\b|vehicle|\bev\b|mobility|bugatti|porsche|aviation',
 'Energy, water & clean power':r'energy|clean power|renewable|solar|\bpower\b|water|\boil\b|utilities|battery|smart meter',
 'Health & life sciences':r'health|biotech|life science|longevity|medicine|pharma|\bhelm\b|bayer',
 'Agrifood & food security':r'agrifood|agri-?food|agricultur|agtech|\bfood|coffee|fmcg|agthia|farm',
 'Real estate & infrastructure':r'real estate|real asset|infrastructure|construction|residential|property|land-lease',
 'Tourism, hospitality & culture':r'touris|hospitality|hotel|\btravel|cultur|museum|luxury',
 'Trade & global partnerships':r'\btrade\b|export|delegation|bilateral|cooperation|\bindia\b|singapore|italy|africa|german|china|france|brics|overseas|cross-border|foreign',
}
# Actor lenses: who the row is about. 'Third-party' = none of the others matched.
ACT={
 'ADIO':r'\badio\b|abu dhabi investment office',
 'ADGM / ADFW':r'adgm|adfw|finance week|financial centre',
 'Sovereign funds':r'mubadala|\badq\b|\badia\b|\bmgx\b|adfd|\bihc\b|\bpif\b|public investment fund|sovereign|trillion fund',
 'ADDED / govt':r'added|department of economic development|mediaoffice|\bwam\b|government|ministry|cabinet|falcon economy',
 'Third-party':None,
}
for r in on:
    r['sect']=[s for s,p in SECT.items() if re.search(p,r['blob'])]
    r['act']=[a for a,p in ACT.items() if p and re.search(p,r['full'] if a=='ADIO' else r['blob'])]
    if not r['act']: r['act']=['Third-party']
adio=[r for r in on if 'ADIO' in r['act']]
print('ADIO',len(adio),[r['i'] for r in adio])
N=len(on);NA=len(adio)
sc={s:sum(1 for r in on if s in r['sect']) for s in SECT}
sa={s:sum(1 for r in adio if s in r['sect']) for s in SECT}
for s in SECT: print(f"{s:36s} all {sc[s]:3d} ({sc[s]/N:.0%})  adio {sa[s]} ({sa[s]/NA:.0%})")
mat={s:{a:sum(1 for r in on if s in r['sect'] and a in r['act']) for a in ACT} for s in SECT}
tot={a:sum(1 for r in on if a in r['act']) for a in ACT}
print(tot)
for s in mat: print(s,list(mat[s].values()))
# ---------------------------------------------------------------- 4. KEYWORD FREQUENCY
ENT=set('investment office adio falcon economy department economic development added abu dhabi uae united arab emirates sheikh mohamed bin zayed nahyan al'.split())
STOP=set('the a an and or of to in for on with by at from as is are was were be been it its this that these those their our we you your he she they his her has have had will can not but also more most into over about than up out new all one two per which who what when where how such other us said says say across through first place explore leading week september press releases latest news videos photos world'.split())|set('https http www com en org html img webp jpg image media amp'.split())
df=collections.Counter();tf=collections.Counter()
for r in on:
    t=re.sub(r'https?://\S+|\]\([^)]*\)','',r['blob'])
    toks=[w for w in re.findall(r"[a-z][a-z\-]{2,}",t) if w not in STOP and w not in ENT]
    tf.update(toks);df.update(set(toks))
top=[(w,df[w],tf[w]) for w in sorted(df,key=lambda w:(-df[w],-tf[w]))[:28]]
print(top)
KW={'fintech':r'fintech','agrifood / agri-food':r'agri-?food|agtech|agricultur','food':r'\bfood','ai':r'\bai\b|artificial intelligence','health / healthcare':r'health','biotech / life sciences':r'biotech|life science','energy':r'\benergy','clean power / renewables':r'clean power|renewable|solar','infrastructure':r'infrastructure','manufacturing / industrial':r'manufactur|industrial','automotive':r'automotive','private equity':r'private equity','insurance / retirement':r'insur|retirement','asset management':r'asset manage|assets under','sukuk':r'sukuk','family offices':r'family office','tourism':r'touris','real estate':r'real estate|real asset','data centres':r'data cent'}
kw={k:(sum(1 for r in on if re.search(p,r['blob'])),sum(len(re.findall(p,r['blob'])) for r in on)) for k,p in KW.items()}
print(sorted(kw.items(),key=lambda x:-x[1][0]))
kwa={k:sum(1 for r in adio if re.search(p,r['blob'])) for k,p in KW.items()}
print(kwa)
# ADIO rows summary
print('\nADIO rows:')
for r in adio: print(' ',r['i'],r['src'],r['title'][:70])

# ---------------------------------------------------------------- 5. HTML TEMPLATE
TEMPLATE = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Abu Dhabi investment discourse: where ADIO sits</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#f2f4f1;--panel:#fff;--ink:#1a2a2e;--mute:#5d6d70;--line:#d5dcd8;--teal:#0d6b70;--gold:#b9812a;--on:#fff;--band:#e8eeea;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1a1c;--panel:#16252a;--ink:#e6eeee;--mute:#93a6a8;--line:#2a3d42;--teal:#4db3ad;--gold:#e0a94f;--on:#06222a;--band:#1b2d32}}
:root[data-theme="dark"]{--bg:#0f1a1c;--panel:#16252a;--ink:#e6eeee;--mute:#93a6a8;--line:#2a3d42;--teal:#4db3ad;--gold:#e0a94f;--on:#06222a;--band:#1b2d32}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:400 15px/1.55 "IBM Plex Sans",system-ui,sans-serif}
main{max-width:920px;margin:0 auto;padding:28px 18px 56px}
h1,h2{font-family:"Source Serif 4",Georgia,serif;font-weight:700;line-height:1.15;margin:0}
h1{font-size:clamp(26px,5vw,38px);max-width:22ch}
h2{font-size:22px;margin-bottom:6px}
p{margin:0 0 10px;max-width:68ch}.lede{color:var(--mute);font-size:16px;margin-top:12px}
section{margin-top:44px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.sub{color:var(--mute);font-size:13px;margin-bottom:12px}
.scroll{overflow-x:auto}
svg{display:block;width:100%;height:auto}
svg text{font-family:"IBM Plex Sans",system-ui,sans-serif;fill:var(--ink)}
table.hm{border-collapse:separate;border-spacing:3px;min-width:640px;width:100%}
.hm th{font-weight:500;font-size:12.5px;color:var(--mute);padding:4px 6px;text-align:center}
.hm th.r{text-align:left;color:var(--ink);font-size:13px;white-space:nowrap}
.hm td{height:40px;text-align:center;font-weight:600;border-radius:5px;background:var(--band);min-width:76px}
.bars div.row{display:grid;grid-template-columns:150px 1fr 60px;gap:10px;align-items:center;margin:5px 0;font-size:13.5px}
.bars .b{height:14px;border-radius:3px;background:var(--teal)}.bars .t{background:var(--band);border-radius:3px}
.bars small{color:var(--mute)}
ul.f{padding-left:0;list-style:none;margin:0}
ul.f li{padding:12px 0;border-top:1px solid var(--line)}ul.f li:first-child{border-top:0}
ul.f b{display:block;margin-bottom:2px}
table.r{width:100%;border-collapse:collapse;font-size:13.5px;min-width:560px}
.r th,.r td{text-align:left;padding:7px 8px;border-top:1px solid var(--line);vertical-align:top}.r th{color:var(--mute);font-weight:500}
a{color:var(--teal)}
.note{font-size:13px;color:var(--mute);border-left:3px solid var(--gold);padding-left:12px;margin-top:14px}
@media(max-width:560px){.bars div.row{grid-template-columns:110px 1fr 50px}}
</style></head><body><main>
<header>
<h1>Abu Dhabi's investment conversation is about finance. ADIO's is about factories, food and health.</h1>
<p class="lede">Text analysis of __RAW__ search results (title and snippet). After removing duplicates and off-topic pages, __N__ rows remain; __NA__ of them mention ADIO or the Abu Dhabi Investment Office.</p>
</header>

<section><h2>Positioning quadrant</h2>
<p class="sub">Across the whole set, each sector's share of rows (horizontal) against ADIO's share of that sector's rows (vertical). Bubble size is the number of ADIO rows in the sector.</p>
<div class="card"><svg id="q" viewBox="0 0 760 520" role="img" aria-label="Quadrant of sectors by discourse volume and ADIO share"></svg></div>
<p class="note">ADIO's overall share is 16% of on-topic rows (8 of 50), so the dashed line marks over- versus under-indexing. Manufacturing, agrifood and automotive rest largely on one Gulf Business interview, so treat them as signals rather than proof.</p>
</section>

<section><h2>Thematic heatmap</h2>
<p class="sub">Rows mentioning each sector, split by who the row is about. Cell shade is the share of that column's rows; the number is the row count. A row can carry several sectors and several lenses.</p>
<div class="card scroll"><table class="hm" id="hm"></table></div>
</section>

<section><h2>Keyword frequency</h2>
<p class="sub">Number of rows containing each term (title plus snippet). Entity names such as "Investment Office" and "Falcon Economy" are excluded.</p>
<div class="card bars" id="kw"></div>
<p class="note">Fintech appears in 3 rows and agrifood in 1, so neither dominates. The most common general terms are capital (17 rows), global (14) and sustainable (10): the discourse is framed around capital and reach, not one sector.</p>
</section>

<section><h2>How ADIO is described</h2>
<div class="card"><ul class="f">
<li><b>An ecosystem builder for industry</b>A Gulf Business interview (23 Sept 2026) presents ADIO as connecting financing, logistics, suppliers and talent so companies can plug in, with automotive, food manufacturing and import substitution as examples.</li>
<li><b>A deal-maker with global corporates</b>Framework agreements with Bayer (health and life sciences) and Prudential Financial (retirement, income and reinsurance).</li>
<li><b>A convenor of capital</b>A July 2025 partnership with the Emirates Family Office Association to attract global family offices, and RealAssetX with ADGM Academy and PGIM.</li>
<li><b>A cross-sector cluster partner</b>Co-led the HELM health and longevity cluster with ADDED and the Department of Health.</li>
<li><b>An arm of ADDED with a new brand</b>Described as the ADDED arm driving diversification and sustainable growth, and a "Beyond Capital" rebrand tied to the Falcon Economy vision.</li>
</ul></div>
<p class="note">Global offices: none of the __NA__ ADIO rows mentions overseas offices or locations. Global reach shows up through partners in Germany and the US, not through an office network. A follow-up search on ADIO's international offices would fill this gap.</p>
<div class="card scroll" style="margin-top:14px"><table class="r" id="ar"><tr><th>Row</th><th>Title</th><th>Source</th></tr></table></div>
</section>

<section><h2>Method</h2>
<p class="sub">__RAW__ rows (71 web, 22 news) reduced to __U__ after removing duplicate titles, then __N__ after dropping off-topic pages (encyclopaedia entries, unrelated market reports, travel and listings). Sectors are keyword-matched on the first 6,000 characters of each row; ADIO is matched on the full text. With this few rows, differences of one or two rows are not meaningful.</p></section>
</main>
<script>
const D=__DATA__;
const $=s=>document.querySelector(s);
const short={'Financial services & capital':'Financial services','AI & digital tech':'AI & digital','Advanced manufacturing & industry':'Advanced manufacturing','Automotive & mobility':'Automotive','Energy, water & clean power':'Energy & water','Health & life sciences':'Health & life sciences','Agrifood & food security':'Agrifood','Real estate & infrastructure':'Real estate & infra','Tourism, hospitality & culture':'Tourism & culture','Trade & global partnerships':'Trade & partnerships'};
// quadrant
(function(){
const W=760,H=520,L=64,R=24,T=26,B=56,xm=50,ym=115,X=v=>L+v/xm*(W-L-R),Y=v=>T+(1-v/ym)*(H-T-B);
const xc=15,yc=D.NA/D.N*100;let s='';
s+=`<rect x="${X(xc)}" y="${T}" width="${W-R-X(xc)}" height="${Y(yc)-T}" fill="var(--teal)" opacity=".07"/>`;
s+=`<rect x="${L}" y="${T}" width="${X(xc)-L}" height="${Y(yc)-T}" fill="var(--gold)" opacity=".10"/>`;
[0,25,50,75,100].forEach(v=>{s+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${L-8}" y="${Y(v)+4}" text-anchor="end" font-size="12" style="fill:var(--mute)">${v}%</text>`});
[0,10,20,30,40,50].forEach(v=>{s+=`<text x="${X(v)}" y="${H-B+18}" text-anchor="middle" font-size="12" style="fill:var(--mute)">${v}%</text>`});
s+=`<line x1="${X(xc)}" x2="${X(xc)}" y1="${T}" y2="${H-B}" stroke="var(--mute)" stroke-dasharray="4 4"/><line x1="${L}" x2="${W-R}" y1="${Y(yc)}" y2="${Y(yc)}" stroke="var(--mute)" stroke-dasharray="4 4"/>`;
s+=`<text x="${L+8}" y="${T+16}" font-size="12.5" font-weight="600" style="fill:var(--gold)">ADIO niches</text>`;
s+=`<text x="${W-R-8}" y="${T+16}" text-anchor="end" font-size="12.5" font-weight="600" style="fill:var(--teal)">Shared ground</text>`;
s+=`<text x="${W-R-8}" y="${H-B-8}" text-anchor="end" font-size="12.5" font-weight="600" style="fill:var(--mute)">Big conversation, ADIO light</text>`;
s+=`<text x="${W/2}" y="${H-10}" text-anchor="middle" font-size="12.5" style="fill:var(--mute)">Share of all on-topic rows mentioning the sector</text>`;
s+=`<text transform="translate(16 ${(T+H-B)/2}) rotate(-90)" text-anchor="middle" font-size="12.5" style="fill:var(--mute)">ADIO share of the sector's rows</text>`;
const off={'Advanced manufacturing & industry':[14,-14,'start'],'Agrifood & food security':[16,26,'start'],'Automotive & mobility':[16,4,'start'],'Health & life sciences':[0,-24,'middle'],'Financial services & capital':[0,-26,'middle'],'AI & digital tech':[-16,-14,'end'],'Energy, water & clean power':[16,16,'start'],'Real estate & infrastructure':[-16,-16,'end'],'Trade & global partnerships':[0,-20,'middle'],'Tourism, hospitality & culture':[0,28,'middle']};
D.sectors.forEach(k=>{const x=D.sc[k]/D.N*100,y=D.sa[k]/D.sc[k]*100,r=6+3*D.sa[k],hi=x<xc&&y>yc;
const [dx,dy,a]=off[k];
s+=`<circle cx="${X(x)}" cy="${Y(y)}" r="${r}" fill="${hi?'var(--gold)':'var(--teal)'}" opacity=".85"/><text x="${X(x)+dx}" y="${Y(y)+dy}" text-anchor="${a}" font-size="12.5">${short[k]}</text>`});
$('#q').innerHTML=s})();
// heatmap
(function(){let h='<tr><th></th>'+D.actors.map(a=>`<th>${a}<br><small>${D.tot[a]} rows</small></th>`).join('')+'</tr>';
D.sectors.forEach(k=>{h+=`<tr><th class="r">${short[k]}</th>`+D.actors.map(a=>{const v=D.mat[k][a],p=v/D.tot[a];
const bg=v?`background:color-mix(in srgb,var(--teal) ${Math.round(12+80*p)}%,transparent);`:'';
const c=p>.5?'color:var(--on);':'';return `<td style="${bg}${c}">${v||''}</td>`}).join('')+'</tr>'});
$('#hm').innerHTML=h})();
// keywords
(function(){const e=Object.entries(D.kw).sort((a,b)=>b[1][0]-a[1][0]||b[1][1]-a[1][1]).slice(0,14),m=e[0][1][0];
$('#kw').innerHTML=e.map(([k,v])=>`<div class="row"><span>${k}</span><div class="t"><div class="b" style="width:${v[0]/m*100}%"></div></div><span>${v[0]} <small>rows</small></span></div>`).join('')})();
// ADIO table
$('#ar').innerHTML+=D.adio.map(r=>`<tr><td>${r.i}</td><td><a href="${r.url}" target="_blank" rel="noopener">${r.title.replace(/</g,'&lt;')}</a></td><td>${r.src}</td></tr>`).join('');
</script></body></html>
'''

# ---------------------------------------------------------------- 6. OUTPUT
out = dict(N=N, NA=NA, raw=len(rows), uniq=len(uniq), sc=sc, sa=sa, mat=mat, tot=tot,
           kw={k: list(v) for k, v in kw.items()}, kwa=kwa,
           adio=[dict(i=r['i'], title=r['title'], url=r['url'], src=r['src']) for r in adio],
           sectors=list(SECT), actors=list(ACT))
with open(os.path.join(args.out_dir, "analysis_data.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

html = (TEMPLATE.replace('__DATA__', json.dumps(out, ensure_ascii=False))
        .replace('__RAW__', str(len(rows))).replace('__N__', str(N))
        .replace('__NA__', str(NA)).replace('__U__', str(len(uniq))))
with open(os.path.join(args.out_dir, "adio_positioning.html"), "w", encoding="utf-8") as fh:
    fh.write(html)
print("Wrote adio_positioning.html and analysis_data.json to", args.out_dir)


