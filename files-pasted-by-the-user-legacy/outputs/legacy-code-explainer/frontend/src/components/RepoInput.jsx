import {useState} from 'react';
export default function RepoInput({onLoad,loading}) { const [url,setUrl]=useState(''); return <form className="repo-input" onSubmit={e=>{e.preventDefault();onLoad(url)}}><input value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://github.com/owner/repository" required/><button disabled={loading}>{loading?'Loading…':'Load repo'}</button></form> }
