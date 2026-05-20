// Read-only card showing a logged interaction with AI-enriched fields

import React from 'react';

const SENTIMENT_STYLE = {
  positive: { color: '#16a34a', background: '#dcfce7' },
  neutral:  { color: '#ca8a04', background: '#fef9c3' },
  negative: { color: '#dc2626', background: '#fee2e2' },
};

const TYPE_LABELS = {
  in_person:  'In-Person',
  phone:      'Phone Call',
  email:      'Email',
  virtual:    'Virtual',
  conference: 'Conference',
};

export default function InteractionCard({ interaction }) {
  if (!interaction) return null;

  const sentimentStyle = SENTIMENT_STYLE[interaction.sentiment] || SENTIMENT_STYLE.neutral;
  const dateStr = new Date(interaction.occurred_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

  return (
    <div className="ic">

      {/* header */}
      <div className="ic-header">
        <div className="ic-header-left">
          <span className="ic-type">
            {TYPE_LABELS[interaction.interaction_type] || interaction.interaction_type}
          </span>
          <span className="ic-date">{dateStr}</span>
          {interaction.duration_minutes && (
            <span className="ic-date">{interaction.duration_minutes} min</span>
          )}
        </div>
        {interaction.sentiment && (
          <span className="ic-sentiment" style={sentimentStyle}>
            {interaction.sentiment.charAt(0).toUpperCase() + interaction.sentiment.slice(1)}
          </span>
        )}
      </div>

      {/* AI summary */}
      {interaction.ai_summary && (
        <div className="ic-summary">
          <div className="ic-summary-label">AI Summary</div>
          <p className="ic-summary-text">{interaction.ai_summary}</p>
        </div>
      )}

      {/* products + topics */}
      <div className="ic-tags-row">
        {interaction.products_discussed?.length > 0 && (
          <div className="ic-tag-group">
            <span className="ic-tag-label">Products</span>
            {interaction.products_discussed.map(p => (
              <span key={p} className="ic-tag ic-tag--product">{p}</span>
            ))}
          </div>
        )}
        {interaction.key_topics?.length > 0 && (
          <div className="ic-tag-group">
            <span className="ic-tag-label">Topics</span>
            {interaction.key_topics.map(t => (
              <span key={t} className="ic-tag">{t}</span>
            ))}
          </div>
        )}
      </div>

      {/* nxt stteps  */}
      {interaction.next_steps && (
        <div className="ic-next-steps">
          <span className="ic-tag-label">Next Steps</span>
          <p className="ic-next-steps-text">{interaction.next_steps}</p>
        </div>
      )}

    </div>
  );
}
