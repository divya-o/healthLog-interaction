// Right panel - conversational interface 
// Messages are stored in Redux , sendChatMessage

import React, { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage, setInput, clearChat } from '../store/chatSlice';
import { patchFormFromAI } from '../store/interactionSlice';

//action label 

const ACTION_LABELS = {
  log_interaction:     'Interaction logged',
  edit_interaction:    'Interaction updated',
  get_hcp_profile:     'HCP profile loaded',
  schedule_followup:   'Follow-up scheduled',
  search_interactions: 'History searched',
};

//message bubble 

function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`chat-msg ${isUser ? 'chat-msg--user' : 'chat-msg--assistant'}`}>
      <div className="chat-bubble">
        {message.content}
        {message.action_taken && (
          <div className="action-badge">
            {ACTION_LABELS[message.action_taken] || message.action_taken}
          </div>
        )}
      </div>
    </div>
  );
}

//typing indicator 

function TypingIndicator() {
  return (
    <div className="chat-msg chat-msg--assistant">
      <div className="chat-bubble typing-bubble">
        <span className="dot" /><span className="dot" /><span className="dot" />
      </div>
    </div>
  );
}

//quick prompt suggestions 

const QUICK_PROMPTS = [
  'Met Dr. Patel today for 30 min, discussed Keytruda dosing',
  'Edit last interaction — duration was 45 minutes',
  'What products did I discuss with Dr. Smith last week?',
  'Schedule a follow-up with this HCP in 2 weeks',
];

//main component 

export default function ChatInterface({ repId }) {
  const dispatch= useDispatch();
  const messages= useSelector(s => s.chat.messages);
  const input= useSelector(s => s.chat.input);
  const status = useSelector(s => s.chat.status);
  const session_id= useSelector(s => s.chat.session_id);
  const hcp_id= useSelector(s => s.interaction.form.hcp_id);
  const isLoading= status === 'loading';

  const bottomRef= useRef(null);
  const textareaRef= useRef(null);

  //scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });}, [messages, isLoading]);

  //resize
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [input]);

  const send = () => {
    const text = input.trim();
    if (!text || isLoading) return;

    dispatch(sendChatMessage({
      message: text,
      hcp_id,
      rep_id: repId,
      session_id,
    }))
      .unwrap()
      .then(res => {
        
        if (res.interaction) {dispatch(patchFormFromAI(res.interaction));}})
      .catch(() => {});

    dispatch(setInput(''));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const applyQuickPrompt = (text) => {
    dispatch(setInput(text));
    textareaRef.current?.focus();
  };

  const showQuickPrompts = messages.length === 1; 

  return (
    <div className="chat-panel">

      {/*  Messages list  */}
      <div className="chat-messages">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isLoading && <TypingIndicator />}

        {showQuickPrompts && (
          <div className="quick-prompts">
            {QUICK_PROMPTS.map(p => (
              <button
                key={p}
                type="button"
                className="quick-prompt-btn"
                onClick={() => applyQuickPrompt(p)}
              >
                {p}
              </button>
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/*  Input bar  */}
      <div className="chat-input-bar">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Describe the interaction or ask a question… (Enter to send)"
          value={input}
          rows={1}
          onChange={e => dispatch(setInput(e.target.value))}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <div className="chat-input-actions">
          <button
            type="button"
            className="btn-icon"
            onClick={() => dispatch(clearChat())}
            title="Clear chat"
          >
            ✕
          </button>
          <button
            type="button"
            className="btn btn--primary btn--send"
            onClick={send}
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? '…' : 'Send'}
          </button>
        </div>
      </div>

    </div>
  );
}
