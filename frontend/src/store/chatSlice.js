import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { chatApi } from '../api/client';

//async thunk 

export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ message, hcp_id, rep_id, session_id }, { rejectWithValue }) => {
    try {
      const res = await chatApi.sendMessage({
        message,
        hcp_id: hcp_id || '00000000-0000-0000-0000-000000000001',
        rep_id: rep_id || 'rep_demo',
        session_id: session_id || null,
      });
      return res.data;                                                    // { reply, interaction, action_taken }
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Agent error');
    }
  }
);

//slice 

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content:
    'Hi! Describe your HCP interaction in plain language and I\'ll log it for you. ' +
    'For example: "Met Dr. Patel today for 30 min, discussed Keytruda dosing, she was receptive."',
  timestamp: new Date().toISOString(),
  action_taken: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [WELCOME_MESSAGE],
    session_id: null,
    input: '',
    status: 'idle',   
    error: null,
  },
  reducers: {
    setInput(state, action) {
      state.input = action.payload;
    },
    clearChat(state) {
      state.messages = [WELCOME_MESSAGE];
      state.session_id = null;
      state.error = null;
      state.input = '';
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state, action) => {
        state.status = 'loading';
        state.error = null;
        //show the user's message
        state.messages.push({
          id: `user-${Date.now()}`,
          role: 'user',
          content: action.meta.arg.message,
          timestamp: new Date().toISOString(),
        });
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'idle';
        state.messages.push({
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: action.payload.reply,
          timestamp: new Date().toISOString(),
          action_taken: action.payload.action_taken,
          interaction_id: action.payload.interaction?.id || null,
        });
        //multi-turn
        if (!state.session_id) {
          state.session_id = `session-${Date.now()}`;
        }
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = 'idle';
        state.error = action.payload;
        state.messages.push({
          id: `error-${Date.now()}`,
          role: 'error',
          content: `Something went wrong: ${action.payload}`,
          timestamp: new Date().toISOString(),
        });
      });
  },
});

export const { setInput, clearChat } = chatSlice.actions;

export default chatSlice.reducer;
