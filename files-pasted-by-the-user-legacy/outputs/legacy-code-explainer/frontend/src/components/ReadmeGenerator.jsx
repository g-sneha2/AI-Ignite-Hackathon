export default function ReadmeGenerator({markdown,onGenerate,loading}){
  return <section>
    <div className="heading">
      <h2>README draft</h2>
      <button onClick={onGenerate} disabled={loading}>{loading?'Generating...':'Generate README'}</button>
    </div>
    {loading && <div className="loader">Explorer is drafting the README…</div>}
    {markdown&&<>
      <button className="copy" onClick={()=>navigator.clipboard.writeText(markdown)}>Copy</button>
      <pre>{markdown}</pre>
    </>}
  </section>;
}
