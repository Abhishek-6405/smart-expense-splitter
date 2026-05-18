import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/api" });

// Users
export const getUsers = () => api.get("/users/");
export const createUser = (data) => api.post("/users/", data);

// Groups
export const getGroups = () => api.get("/groups/");
export const createGroup = (data) => api.post("/groups/", data);
export const getGroup = (id) => api.get(`/groups/${id}`);

// Expenses
export const getExpenses = (gid, params) =>
  api.get(`/groups/${gid}/expenses`, { params });
export const createExpense = (gid, data) =>
  api.post(`/groups/${gid}/expenses`, data);
export const deleteExpense = (gid, eid) =>
  api.delete(`/groups/${gid}/expenses/${eid}`);

// Balances
export const getBalances = (gid) => api.get(`/groups/${gid}/balances`);
export const getSettleUp = (gid) => api.get(`/groups/${gid}/settle-up`);
export const createSettlement = (gid, data) =>
  api.post(`/groups/${gid}/settlements`, data);

// AI
export const parseExpense = (data) => api.post("/ai/parse-expense", data);
export const parseBill = (data) => api.post("/ai/parse-bill", data);