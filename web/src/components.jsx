import React from 'react';

export const repo = 'https://github.com/pzg8794/sandai-seminar-operations-demo';
export const percent = value => `${Math.round(value * 100)}%`;
export function download(name, text, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([text], {type}));
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function Card({title, sub, children, className = '', id}) {
  return <section id={id} className={`card ${className}`}><header><h2>{title}</h2>{sub && <p>{sub}</p>}</header>{children}</section>;
}
export function KPI({label, value, detail}) {
  return <div className="kpi"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}
