import { useState, useCallback } from 'react';

function Node({ node, onSelect, selected, expanded, toggle }) {
	if (node.type === 'file') {
		return (
			<button
				className={'file ' + (selected === node.path ? 'selected' : '')}
				onClick={() => onSelect(node.path)}
			>
				<i className={node.risk_score} />
				{node.path.split('/').pop()}
			</button>
		);
	}

	const name = node.path.split('/').pop();
	const isOpen = expanded.has(node.path);

	return (
		<div className="folder">
			<div className="folder-header" onClick={() => toggle(node.path)}>
				<span className={isOpen ? 'open' : 'closed'}>{isOpen ? '▾' : '▸'}</span>
				<span className="folder-name">{name}</span>
			</div>
			{isOpen && (
				<div className="nested">
					{node.children.map((c) => (
						<Node key={c.path} node={c} onSelect={onSelect} selected={selected} expanded={expanded} toggle={toggle} />
					))}
				</div>
			)}
		</div>
	);
}

function collectDirs(nodes, out = []) {
	for (const n of nodes) {
		if (n.type !== 'file') {
			out.push(n.path);
			if (n.children) collectDirs(n.children, out);
		}
	}
	return out;
}

export default function FileTree({ tree = [], onSelect, selected }) {
	const [expanded, setExpanded] = useState(new Set());

	const toggle = useCallback((path) => {
		setExpanded((s) => {
			const next = new Set(s);
			if (next.has(path)) next.delete(path);
			else next.add(path);
			return next;
		});
	}, []);

	const expandAll = () => {
		const dirs = collectDirs(tree);
		setExpanded(new Set(dirs));
	};

	const collapseAll = () => setExpanded(new Set());

	return (
		<aside>
			<h2>Python files</h2>
			<p className="legend">
				<i className="green" /> low <i className="yellow" /> medium <i className="red" /> high
			</p>

			<div className="tree-controls">
				<button onClick={collapseAll}>Collapse all</button>
				<button onClick={expandAll}>Expand all</button>
			</div>

			{tree.map((n) => (
				<Node key={n.path} node={n} onSelect={onSelect} selected={selected} expanded={expanded} toggle={toggle} />
			))}
		</aside>
	);
}
