import {useState} from 'react';
import api from './api/client';
import RepoInput from './components/RepoInput';
import FileTree from './components/FileTree';
import ExplanationPanel from './components/ExplanationPanel';
import DependencyGraph from './components/DependencyGraph';
import RiskWarning from './components/RiskWarning';
import OnboardingPath from './components/OnboardingPath';
import ReadmeGenerator from './components/ReadmeGenerator';
import ChatPanel from './components/ChatPanel';

const tabs=['Explain','Graph','Risk','Path','README','Ask'];

export default function App(){
  const [repo,setRepo]=useState(null),
    [selected,setSelected]=useState(null),
    [tab,setTab]=useState('Explain'),
    [loading,setLoading]=useState(false),
    [busy,setBusy]=useState({load:false, explain:false, graph:false, risk:false, path:false, readme:false, ask:false}),
    [error,setError]=useState(''),
    [explain,setExplain]=useState(),
    [graph,setGraph]=useState(),
    [risk,setRisk]=useState(),
    [path,setPath]=useState(),
    [readme,setReadme]=useState(),
    [messages,setMessages]=useState([]);

  const runRequest = async (key, fn) => {
    setBusy(b => ({...b, [key]: true}));
    try {
      return await fn();
    } finally {
      setBusy(b => ({...b, [key]: false}));
    }
  };

  const call=async(fn)=>{try{setError('');return await fn()}catch(e){setError(e.response?.data?.detail||'Something went wrong. Check that the API server is running.')}};

  const load=async url=>{
    setLoading(true);
    const data = await runRequest('load', async()=> await call(async()=> (await api.post('/load-repo',{repo_url:url})).data));
    setLoading(false);
    if(data){setRepo(data);setSelected(null);setExplain();setGraph();setRisk();setPath();setReadme();setMessages([])}
  };

  const choose=async file=>{
    setSelected(file);
    setRisk();
    const data = await runRequest('explain', async()=> await call(async()=> (await api.post('/explain-file',{repo_id:repo.repo_id,file_path:file})).data));
    if(data)setExplain(data);
  };

  const activate=async name=>{
    setTab(name);
    if(!repo)return;
    if(name==='Graph'&&selected){
      const d = await runRequest('graph', async()=> await call(async()=> (await api.post('/dependency-graph',{repo_id:repo.repo_id,file_path:selected})).data));
      if(d)setGraph(d.mermaid_syntax);
    }
    if(name==='Path'&&!path){
      const d = await runRequest('path', async()=> await call(async()=> (await api.post('/onboarding-path',{repo_id:repo.repo_id})).data));
      if(d)setPath(d.path);
    }
  };

  const checkRisk=async function_name=>{
    const d = await runRequest('risk', async()=> await call(async()=> (await api.post('/risk-check',{repo_id:repo.repo_id,file_path:selected,function_name})).data));
    if(d)setRisk(d);
  };

  const generate=async()=>{
    const d = await runRequest('readme', async()=> await call(async()=> (await api.post('/generate-readme',{repo_id:repo.repo_id})).data));
    if(d)setReadme(d.readme_markdown);
  };

  const ask=async question=>{
    setMessages(m=>[...m,{role:'user',text:question}]);
    const d = await runRequest('ask', async()=> await call(async()=> (await api.post('/ask',{repo_id:repo.repo_id,question})).data));
    if(d)setMessages(m=>[...m,{role:'assistant',text:d.answer,sources:d.sources}]);
  };

  return <main>
    <header>
      <div>
        <span className="eyebrow">CODEBASE INTELLIGENCE</span>
        <h1>Legacy Code Explorer</h1>
        <p>Understand unfamiliar Python repositories, without the archaeology.</p>
      </div>
      <RepoInput onLoad={load} loading={loading}/>
    </header>
    {error&&<div className="error">{error}</div>}
    {repo?
      <div className="workspace">
        <FileTree tree={repo.file_tree} onSelect={choose} selected={selected}/>
        <article>
          <nav>{tabs.map(t=><button className={tab===t?'active':''} onClick={()=>activate(t)} key={t}>{t}</button>)}</nav>
          <div className="panel">
            {tab==='Explain'&&<ExplanationPanel data={explain} loading={busy.explain}/>}
            {tab==='Graph'&&<DependencyGraph syntax={graph} loading={busy.graph}/>}
            {tab==='Risk'&&<RiskWarning functions={explain?.functions} onCheck={checkRisk} data={risk} loading={busy.risk}/>}
            {tab==='Path'&&<OnboardingPath items={path} loading={busy.path}/>}
            {tab==='README'&&<ReadmeGenerator markdown={readme} onGenerate={generate} loading={busy.readme}/>}
            {tab==='Ask'&&<ChatPanel messages={messages} onAsk={ask} loading={busy.ask}/>}
          </div>
        </article>
      </div>
      :
      <div className="empty"><h2>Start with a public GitHub repository</h2><p>We’ll map its Python files, their connections, and the riskiest areas to change.</p></div>
    }
  </main>;
}
