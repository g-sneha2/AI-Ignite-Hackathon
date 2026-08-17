import {useEffect,useRef,useState} from 'react';

// Load the optional renderer only after a graph has been requested, so it
// cannot keep the main interface from mounting.
export default function DependencyGraph({syntax}) {
  const ref=useRef(); const [error,setError]=useState('');
  useEffect(()=>{ let active=true; if(!syntax)return;
    import('mermaid').then(({default:mermaid})=>{mermaid.initialize({startOnLoad:false,theme:'neutral'});return mermaid.render('graph-'+Date.now(),syntax)})
      .then(({svg})=>{if(active&&ref.current)ref.current.innerHTML=svg})
      .catch(()=>active&&setError('Unable to render this dependency graph.'));
    return()=>{active=false}
  },[syntax]);
  return <section><h2>Dependency graph</h2>{error?<p className="error">{error}</p>:syntax?<div className="graph" ref={ref}/>:<p>Select a file to generate its dependency graph.</p>}</section>
}
