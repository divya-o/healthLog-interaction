// Left panel — structured form for logging HCP interactions.

import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  updateField,
  addAttendee,
  removeAttendee,
  addProduct,
  removeProduct,
  submitInteractionForm,
  resetForm,
} from '../store/interactionSlice';
import { hcpApi } from '../api/client';

//  Small reusable pieces 

function FieldLabel({ children, required }) {
  return (
    <label className="field-label">
      {children}
      {required && <span className="required-star">*</span>}
    </label>
  );
}

function Tag({ label, onRemove }) {
  return (
    <span className="tag">
      {label}
      <button type="button" className="tag-remove" onClick={onRemove}>×</button>
    </span>
  );
}

//HCP autocomplete search 

function HCPSearch() {
  const dispatch = useDispatch();
  const hcpName = useSelector(s => s.interaction.form.hcp_name);
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef(null);

  const handleChange = (e) => {
    const val = e.target.value;
    dispatch(updateField({ field: 'hcp_name', value: val }));
    dispatch(updateField({ field: 'hcp_id', value: '' }));

    clearTimeout(debounceRef.current);
    if (val.length < 2) { setSuggestions([]); setOpen(false); return; }

    debounceRef.current = setTimeout(async () => {
      try {
        const res = await hcpApi.search(val);
        setSuggestions(res.data);
        setOpen(true);
      } catch {
        setSuggestions([]);
      }
    }, 300);
  };

  const select = (hcp) => {
    dispatch(updateField({ field: 'hcp_id', value: hcp.id }));
    dispatch(updateField({ field: 'hcp_name', value: hcp.full_name }));
    setOpen(false);
  };

  return (
    <div className="autocomplete-wrapper">
      <input
        type="text"
        className="form-input"
        placeholder="Search HCP by name..."
        value={hcpName}
        onChange={handleChange}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        autoComplete="off"
      />
      {open && suggestions.length > 0 && (
        <div className="dropdown-list">
          {suggestions.map((hcp) => (
            <div key={hcp.id} className="dropdown-item" onMouseDown={() => select(hcp)}>
              <span className="dropdown-name">{hcp.full_name}</span>
              <span className="dropdown-meta">{hcp.specialty} · {hcp.territory}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Interaction type options 

const INTERACTION_TYPES = [
  { value: 'in_person',   label: 'In-Person Meeting' },
  { value: 'phone',       label: 'Phone Call' },
  { value: 'email',       label: 'Email' },
  { value: 'virtual',     label: 'Virtual / Video' },
  { value: 'conference',  label: 'Conference' },
];


export default function StructuredForm({ repId }) {
  const dispatch = useDispatch();
  const form     = useSelector(s => s.interaction.form);
  const status   = useSelector(s => s.interaction.status);
  const error    = useSelector(s => s.interaction.error);

  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (status === 'succeeded') {
      setShowSuccess(true);
      const t = setTimeout(() => setShowSuccess(false), 4000);
      return () => clearTimeout(t);
    }
  }, [status]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.hcp_id || status === 'loading') return;

    const occurred_at = new Date(
      `${form.occurred_at}T${form.time || '09:00'}`
    ).toISOString();

    // Combine topics 
    const raw_notes = [form.topics_discussed, form.raw_notes]
      .filter(Boolean)
      .join('\n\n') || null;

    dispatch(submitInteractionForm({
      hcp_id:            form.hcp_id,
      rep_id:            repId,
      interaction_type:  form.interaction_type,
      occurred_at,
      location:          form.location || null,
      duration_minutes:  form.duration_minutes ? parseInt(form.duration_minutes) : null,
      raw_notes,
      products_discussed: form.products_discussed.length ? form.products_discussed : null,
      next_steps:        form.next_steps || null,
    }));
  };

  return (
    <form className="structured-form" onSubmit={handleSubmit} noValidate>

      {/*  Feedback banners  */}
      {showSuccess && (
        <div className="banner banner--success">
          ✓ Interaction logged and AI summary generated.
        </div>
      )}
      {error && (
        <div className="banner banner--error">{error}</div>
      )}

      {/*  Section: Interaction Details  */}
      <div className="form-section">
        <div className="section-label">Interaction Details</div>

        <div className="form-row two-col">
          <div className="form-field">
            <FieldLabel required>HCP Name</FieldLabel>
            <HCPSearch />
          </div>
          <div className="form-field">
            <FieldLabel required>Interaction Type</FieldLabel>
            <select
              className="form-input"
              value={form.interaction_type}
              onChange={e => dispatch(updateField({ field: 'interaction_type', value: e.target.value }))}
            >
              {INTERACTION_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row two-col">
          <div className="form-field">
            <FieldLabel required>Date</FieldLabel>
            <input
              type="date"
              className="form-input"
              value={form.occurred_at}
              onChange={e => dispatch(updateField({ field: 'occurred_at', value: e.target.value }))}
            />
          </div>
          <div className="form-field">
            <FieldLabel>Time</FieldLabel>
            <input
              type="time"
              className="form-input"
              value={form.time}
              onChange={e => dispatch(updateField({ field: 'time', value: e.target.value }))}
            />
          </div>
        </div>

        <div className="form-row two-col">
          <div className="form-field">
            <FieldLabel>Location</FieldLabel>
            <input
              type="text"
              className="form-input"
              placeholder="Clinic, office, virtual..."
              value={form.location}
              onChange={e => dispatch(updateField({ field: 'location', value: e.target.value }))}
            />
          </div>
          <div className="form-field">
            <FieldLabel>Duration (mins)</FieldLabel>
            <input
              type="number"
              className="form-input"
              placeholder="30"
              min="1"
              max="480"
              value={form.duration_minutes}
              onChange={e => dispatch(updateField({ field: 'duration_minutes', value: e.target.value }))}
            />
          </div>
        </div>
      </div>

      <div className="form-divider" />

      {/*  Section: Attendees  */}
      <div className="form-section">
        <div className="section-label">Attendees</div>
        <div className="tag-input-row">
          <input
            type="text"
            className="form-input"
            placeholder="Type name and press Enter..."
            value={form.attendee_input}
            onChange={e => dispatch(updateField({ field: 'attendee_input', value: e.target.value }))}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); dispatch(addAttendee()); } }}
          />
        </div>
        <div className="tag-list">
          {form.attendees.map(a => (
            <Tag key={a} label={a} onRemove={() => dispatch(removeAttendee(a))} />
          ))}
        </div>
      </div>

      <div className="form-divider" />

      {/*  Section: Topics  */}
      <div className="form-section">
        <div className="section-label">Discussion Notes</div>
        <FieldLabel>Topics Discussed</FieldLabel>
        <textarea
          className="form-input form-textarea"
          placeholder="Key points covered in this interaction..."
          rows={4}
          value={form.topics_discussed}
          onChange={e => dispatch(updateField({ field: 'topics_discussed', value: e.target.value }))}
        />
      </div>

      <div className="form-divider" />

      {/*  Section: Products / Materials  */}
      <div className="form-section">
        <div className="section-label">Materials Shared / Products Discussed</div>
        <div className="tag-input-row">
          <input
            type="text"
            className="form-input"
            placeholder="Type product/material and press Enter..."
            value={form.product_input}
            onChange={e => dispatch(updateField({ field: 'product_input', value: e.target.value }))}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); dispatch(addProduct()); } }}
          />
        </div>
        <div className="tag-list">
          {form.products_discussed.length === 0
            ? <span className="muted-text">No products added yet.</span>
            : form.products_discussed.map(p => (
                <Tag key={p} label={p} onRemove={() => dispatch(removeProduct(p))} />
              ))
          }
        </div>
      </div>

      <div className="form-divider" />

      {/*  Section: Next Steps  */}
      <div className="form-section">
        <FieldLabel>Next Steps / Follow-up</FieldLabel>
        <textarea
          className="form-input form-textarea"
          placeholder="e.g., Send clinical data, schedule follow-up in 2 weeks..."
          rows={3}
          value={form.next_steps}
          onChange={e => dispatch(updateField({ field: 'next_steps', value: e.target.value }))}
        />
      </div>

      {/*  Actions  */}
      <div className="form-actions">
        <button
          type="button"
          className="btn btn--secondary"
          onClick={() => dispatch(resetForm())}
        >
          Clear
        </button>
        <button
          type="submit"
          className="btn btn--primary"
          disabled={!form.hcp_id || status === 'loading'}
        >
          {status === 'loading' ? 'Saving…' : 'Log Interaction'}
        </button>
      </div>

    </form>
  );
}
