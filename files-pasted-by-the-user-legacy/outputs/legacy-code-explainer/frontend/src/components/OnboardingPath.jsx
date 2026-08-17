export default function OnboardingPath({items,loading}){
  if(loading) return <section><h2>New engineer reading path</h2><div className="loader">Explorer is building a reading path…</div></section>;
  if(!items) return <section><h2>New engineer reading path</h2><p>Open this tab to create a reading path.</p></section>;

  return <section>
    <h2>New engineer reading path</h2>
    <ol>
      {items.map((x,i)=><li key={i}><b>{x.file}</b>
        <div className="path-reason">
          {(x.reason || '').split(/\n+/).filter(Boolean).map((paragraph, idx)=><p key={idx}>{paragraph}</p>)}
        </div>
      </li>)}
    </ol>
  </section>;
}
