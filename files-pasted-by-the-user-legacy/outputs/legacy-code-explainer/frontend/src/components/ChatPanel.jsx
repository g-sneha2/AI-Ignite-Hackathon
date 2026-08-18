import {useState} from 'react';
export default function ChatPanel({messages,onAsk,loading,repoName}){
	const [q,setQ]=useState('');
	return (
		<section className="chat">
			<div className="chat-header">
				<h2>Explorer Chat</h2>
				{repoName && <small className="repo-name">{repoName}</small>}
			</div>
			{loading && <div className="loader">Explorer is thinking…</div>}
			<div className="messages">{messages.map((m,i)=>(
				<div className={m.role} key={i}>
					<b>{m.role==='user'?'You':'Explorer'}</b>
					<p>{m.text}</p>
					{m.sources&&<small>Sources: {m.sources.join(', ')}</small>}
				</div>
			))}</div>
			<form className="chat-input" onSubmit={e=>{e.preventDefault();if(q.trim()&&!loading){onAsk(q);setQ('')}}}>
				<input value={q} onChange={e=>setQ(e.target.value)} placeholder={repoName?`Ask about ${repoName} or the selected file…`:'Ask about this codebase…'} disabled={loading}/>
				<button disabled={loading}>{loading?'Waiting...':'Ask'}</button>
			</form>
		</section>
	);
}
