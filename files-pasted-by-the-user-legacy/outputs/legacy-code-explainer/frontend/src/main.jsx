import React from 'react'; import {createRoot} from 'react-dom/client'; import App from './App'; import './index.css';
class AppErrorBoundary extends React.Component {
  constructor(props){super(props);this.state={error:null}}
  static getDerivedStateFromError(error){return {error}}
  render(){return this.state.error ? <main className="empty"><h2>Unable to start the interface</h2><p>{this.state.error.message}</p></main> : this.props.children}
}
createRoot(document.getElementById('root')).render(<AppErrorBoundary><App/></AppErrorBoundary>);
