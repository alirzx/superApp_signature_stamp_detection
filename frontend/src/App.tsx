import { useEffect, useState } from 'react';

type Box = { x1:number; y1:number; x2:number; y2:number };
type Detection = { object_id:string; type:'stamp'|'signature'; bbox:Box; confidence:number };
type DetectResult = { image:{ source_width:number; source_height:number }; objects:Detection[]; counts:{stamp:number;signature:number}; processing_time_ms:number; request_id:string; warnings:string[] };

export default function App(){
  const [file, setFile] = useState<File|null>(null);
  const [preview, setPreview] = useState('');
  const [result, setResult] = useState<DetectResult|null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiReady, setApiReady] = useState<boolean|null>(null);
  const [threshold, setThreshold] = useState(0.5);
  const [filter, setFilter] = useState<'all'|'stamp'|'signature'>('all');
  useEffect(()=>{
    let disposed=false;
    async function poll(){
      try{const r=await fetch('/api/health/ready',{cache:'no-store'});if(!disposed)setApiReady(r.ok);}
      catch{if(!disposed)setApiReady(false);}
    }
    void poll();const id=window.setInterval(()=>void poll(),20000);
    return()=>{disposed=true;window.clearInterval(id)};
  },[]);
  useEffect(()=>{if(!file){setPreview('');return;} const url=URL.createObjectURL(file);setPreview(url);return()=>URL.revokeObjectURL(url);},[file]);
  async function detect(){
    if(!file)return;
    setError('');setResult(null);setLoading(true);
    try{
      const form = new FormData();form.append('file',file);form.append('threshold',String(threshold));
      const response = await fetch('/api/v1/detect',{method:'POST',body:form});
      if(!response.ok){const body=await response.json().catch(()=>({detail:response.statusText})); throw new Error(String(body.detail||'Detection failed'));}
      setResult(await response.json() as DetectResult);
    }catch(e){setError(e instanceof Error?e.message:'Request failed');}
    finally{setLoading(false);}
  }
  const shown = result?.objects.filter(o=>filter==='all'||o.type===filter) || [];
  return <main className="shell">
    <header><div className="badge">SUPERAPP · MODULE 06</div><h1>شناسایی مهر و امضا</h1><p>شناسایی جایگاه مهر و امضا در تصاویر اسناد، با مدل RF-DETR و پردازش CPU</p></header>
    {apiReady===false&&<div className="error" role="status">سرویس تشخیص هنوز آماده نیست. صفحه فعال است؛ وضعیت API به طور خودکار بررسی می‌شود.</div>}
    <section className="grid">
      <div className="panel controls">
        <h2>تصویر سند</h2>
        <label className="drop" htmlFor="upload"><span>تصویر را انتخاب کنید</span><small>JPG, PNG, WebP · حداکثر ۱۰ مگابایت</small></label>
        <input id="upload" type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>{setFile(e.target.files?.[0]||null);setResult(null);setError('');}} />
        <label className="field">حداقل اطمینان: {Math.round(threshold*100)}٪ <input type="range" min="0.1" max="0.95" step="0.05" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/></label>
        <button onClick={detect} disabled={!file||loading||apiReady===false}>{loading?'در حال پردازش...':'شناسایی مهر و امضا'}</button>
        {error&&<p className="error" role="alert">{error}</p>}
        <p className="hint">فقط مختصات مهر و امضا گزارش می‌شود. محتوای اسناد ذخیره نمی‌شود.</p>
        {result&&<div className="summary"><div><strong>{result.counts.stamp}</strong><span>مهر</span></div><div><strong>{result.counts.signature}</strong><span>امضا</span></div><div><strong>{Math.round(result.processing_time_ms)}</strong><span>ms</span></div></div>}
      </div>
      <div className="panel canvas-panel">
        <div className="toolbar"><h2>نمایش نتیجه</h2><select aria-label="نوع تشخیص" value={filter} onChange={e=>setFilter(e.target.value as typeof filter)}><option value="all">همه</option><option value="stamp">فقط مهر</option><option value="signature">فقط امضا</option></select></div>
        {preview ? <div className="image-area"><div className="preview"><img src={preview} alt="تصویر سند" />{result&&shown.map(obj=><div key={obj.object_id} className={'bbox '+obj.type} style={{left:`${obj.bbox.x1/result.image.source_width*100}%`,top:`${obj.bbox.y1/result.image.source_height*100}%`,width:`${(obj.bbox.x2-obj.bbox.x1)/result.image.source_width*100}%`,height:`${(obj.bbox.y2-obj.bbox.y1)/result.image.source_height*100}%`}}><span>{obj.type==='stamp'?'مهر':'امضا'} · {Math.round(obj.confidence*100)}٪</span></div>)}</div></div>:<div className="empty">تصویر سند در اینجا نمایش داده می‌شود</div>}
        {result&&<div className="results"><h3>اشیای شناسایی‌شده ({shown.length})</h3>{shown.length ? shown.map((o,i)=><div className="row" key={o.object_id}><b>{i+1}. {o.type==='stamp'?'مهر':'امضا'}</b><span>اطمینان: {Math.round(o.confidence*100)}٪</span><code dir="ltr">{Object.values(o.bbox).map(Math.round).join(', ')}</code></div>):<p>موردی در این دسته یافت نشد.</p>}<button className="secondary" onClick={()=>{const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='detections.json';a.click();URL.revokeObjectURL(url);}}>دانلود JSON</button></div>}
      </div>
    </section><footer>SuperApp · Signature & Stamp Detection · CPU inference</footer>
  </main>;
}