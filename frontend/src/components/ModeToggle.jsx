// Toggle switch between "Structured Form" and "AI Chat" modes

import React from 'react';

export default function ModeToggle({ mode, onChange }) {
  return (
    <div className="mode-toggle" role="group" aria-label="Input mode">
      <button
        type="button"
        className={`mode-toggle__btn ${mode === 'form' ? 'mode-toggle__btn--active' : ''}`}
        onClick={() => onChange('form')}
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
          <rect x="1" y="2" width="14" height="2.5" rx="1" fill="currentColor" opacity="0.8" />
          <rect x="1" y="6.75" width="10" height="2.5" rx="1" fill="currentColor" opacity="0.6" />
          <rect x="1" y="11.5" width="12" height="2.5" rx="1" fill="currentColor" opacity="0.4" />
        </svg>
        Structured Form
      </button>

      <button
        type="button"
        className={`mode-toggle__btn ${mode === 'chat' ? 'mode-toggle__btn--active' : ''}`}
        onClick={() => onChange('chat')}
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
          <path
            d="M14 2H2a1 1 0 00-1 1v8a1 1 0 001 1h3l2 2 2-2h5a1 1 0 001-1V3a1 1 0 00-1-1z"
            stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"
          />
          <circle cx="5.5" cy="7" r="0.8" fill="currentColor" />
          <circle cx="8" cy="7" r="0.8" fill="currentColor" />
          <circle cx="10.5" cy="7" r="0.8" fill="currentColor" />
        </svg>
        AI Chat
      </button>
    </div>
  );
}
