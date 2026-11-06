import React from 'react'
import ReactMarkdown from 'react-markdown'

export default function MarkdownContent({ content, className = '' }) {
  if (!content) return null

  return (
    <div className={`markdown-body ${className}`}>
      <ReactMarkdown
        components={{
          h1: ({ node, ...props }) => (
            <h1 className="text-base font-bold text-slate-900 mt-3 mb-1.5" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-sm font-bold text-slate-900 mt-2.5 mb-1 text-brand-700" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-sm font-semibold text-slate-800 mt-2 mb-1" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="my-1.5 leading-relaxed" {...props} />
          ),
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-slate-900 bg-amber-50/50 px-0.5 rounded" {...props} />
          ),
          em: ({ node, ...props }) => (
            <em className="italic" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc pl-5 my-1.5 space-y-1" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal pl-5 my-1.5 space-y-1" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="leading-relaxed" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-brand-400 pl-3 italic my-2 text-slate-600 bg-slate-50 py-1 rounded-r" {...props} />
          ),
          code: ({ node, inline, ...props }) => (
            inline ? (
              <code className="bg-slate-200/70 text-slate-800 px-1.5 py-0.5 rounded font-mono text-xs" {...props} />
            ) : (
              <pre className="bg-slate-800 text-slate-100 p-3 rounded-lg overflow-x-auto text-xs my-2 font-mono">
                <code {...props} />
              </pre>
            )
          ),
          hr: ({ node, ...props }) => (
            <hr className="my-3 border-slate-200" {...props} />
          ),
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full divide-y divide-slate-200 text-xs border border-slate-200 rounded-lg" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-slate-50 font-semibold text-slate-700" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="px-3 py-2 text-left border-b border-slate-200" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="px-3 py-1.5 border-b border-slate-100 text-slate-700" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

