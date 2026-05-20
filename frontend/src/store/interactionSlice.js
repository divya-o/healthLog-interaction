import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { interactionsApi } from '../api/client';

//async thunks 
export const submitInteractionForm = createAsyncThunk(
  'interaction/submit',
  async (payload, { rejectWithValue }) => {
    try {
      const res = await interactionsApi.create(payload);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Submission failed');
    }
  }
);

//initial load to populate the recent interactions list
export const fetchInteractions = createAsyncThunk(
  'interaction/fetchAll',
  async (params = {}, { rejectWithValue }) => {
    try {
      const res = await interactionsApi.list(params);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load interactions');
    }
  }
);

//editing via the form
export const updateInteraction = createAsyncThunk(
  'interaction/update',
  async ({ id, data }, { rejectWithValue }) => {
    try {
      const res = await interactionsApi.update(id, data);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Update failed');
    }
  }
);

//initial form state 

const EMPTY_FORM = {
  hcp_id: '',
  hcp_name: '',             // display-only, not sent to API
  interaction_type: 'in_person',
  occurred_at: new Date().toISOString().slice(0, 10),
  time: new Date().toTimeString().slice(0, 5),
  location: '',
  duration_minutes: '',
  attendees: [],
  attendee_input: '',
  topics_discussed: '',
  raw_notes: '',
  products_discussed: [],
  product_input: '',
  next_steps: '',
};

const interactionSlice = createSlice({
  name: 'interaction',
  initialState: {
    form: { ...EMPTY_FORM },
    interactions: [],         
    lastSaved: null,          
    status: 'idle',           
    error: null,
  },
  reducers: {
    // Update any single form field by name
    updateField(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    addAttendee(state) {
      const name = state.form.attendee_input.trim();
      if (name && !state.form.attendees.includes(name)) {
        state.form.attendees.push(name);
      }
      state.form.attendee_input = '';
    },
    removeAttendee(state, action) {
      state.form.attendees = state.form.attendees.filter(a => a !== action.payload);
    },
    addProduct(state) {
      const p = state.form.product_input.trim();
      if (p && !state.form.products_discussed.includes(p)) {
        state.form.products_discussed.push(p);
      }
      state.form.product_input = '';
    },
    removeProduct(state, action) {
      state.form.products_discussed = state.form.products_discussed.filter(
        p => p !== action.payload
      );
    },
    resetForm(state) {
      state.form = { ...EMPTY_FORM };
      state.status = 'idle';
      state.error = null;
    },
    clearInteractions(state) {
      state.interactions = [];
      state.lastSaved = null;
    },
    //sync form fields when the AI chat logs an interaction
    patchFormFromAI(state, action) {
      const data = action.payload;
      if (data.hcp_id)    state.form.hcp_id = data.hcp_id;
      if (data.interaction_type)  state.form.interaction_type = data.interaction_type;
      if (data.raw_notes)  state.form.raw_notes = data.raw_notes;
      if (data.products_discussed) state.form.products_discussed = data.products_discussed;
      if (data.next_steps) state.form.next_steps = data.next_steps;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitInteractionForm.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(submitInteractionForm.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.interactions.unshift(action.payload);
        state.lastSaved = action.payload;
        state.form = { ...EMPTY_FORM };
      })
      .addCase(submitInteractionForm.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.interactions = action.payload;
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.interactions.findIndex(i => i.id === action.payload.id);
        if (idx !== -1) state.interactions[idx] = action.payload;
        state.lastSaved = action.payload;
      });
  },
});

export const {
  updateField,
  addAttendee,
  removeAttendee,
  addProduct,
  removeProduct,
  resetForm,
  clearInteractions,
  patchFormFromAI,
} = interactionSlice.actions;

export default interactionSlice.reducer;
