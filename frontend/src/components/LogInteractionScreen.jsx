// Main screen: side-by-side layout - Structured Form (left) + AI Chat (right)

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchInteractions } from '../store/interactionSlice';
import StructuredForm from './StructuredForm';
import ChatInterface from './ChatInterface';
import ModeToggle from './ModeToggle';
import InteractionCard from './InteractionCard';

export default function LogInteractionScreen({ repId }) {
  const dispatch = useDispatch();
  const lastSaved = useSelector(s => s.interaction.lastSaved);

  // Mobile: start on form, allow toggling to chat
  const [mobileMode, setMobileMode] = useState('form');

  // Fetch recent interactions on mount so the list is populated
  useEffect(() => {
    dispatch(fetchInteractions({ rep_id: repId, limit: 5 }));
  }, [dispatch, repId]);

  return (
    <div className="screen-root">

      {/*  Top navbar  */}
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="brand-dot" />
          <span className="brand-name">HCP CRM</span>
          <span className="brand-divider">|</span>
          <span className="brand-module">Log Interaction</span>
        </div>
        <div className="navbar-right">
          <span className="nav-rep">{repId}</span>
          <div className="avatar-circle">
            {repId[0].toUpperCase()}
          </div>
        </div>
      </nav>

      {/*  Page header  */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Log HCP Interaction</h1>
          <p className="page-subtitle">
            Use the structured form or describe the interaction in natural language via the AI assistant.
          </p>
        </div>
        {/* ModeToggle only visible on mobile */}
        <div className="mobile-only">
          <ModeToggle mode={mobileMode} onChange={setMobileMode} />
        </div>
      </div>

      {/*  Split layout  */}
      <div className="split-layout">

        {/* Left — Structured Form */}
        <div className={`split-left ${mobileMode === 'chat' ? 'mobile-hidden' : ''}`}>
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Structured Form</h2>
              <span className="panel-badge panel-badge--form">Form</span>
            </div>
            <StructuredForm repId={repId} />
          </div>
        </div>

        {/* Right — AI Chat */}
        <div className={`split-right ${mobileMode === 'form' ? 'mobile-hidden' : ''}`}>
          <div className="panel panel--chat">
            <div className="panel-header">
              <h2 className="panel-title">AI Assistant</h2>
              <span className="panel-badge panel-badge--ai">Groq · gemma2-9b-it</span>
            </div>
            <ChatInterface repId={repId} />
          </div>
        </div>

      </div>

      {/*  Last logged interaction preview  */}
      {lastSaved && (
        <div className="recent-section">
          <h3 className="recent-title">Last Logged Interaction</h3>
          <InteractionCard interaction={lastSaved} />
        </div>
      )}

    </div>
  );
}
