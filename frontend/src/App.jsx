import { useEffect, useState } from "react";
import { api } from "./api";
import "./App.css";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

function App() {
  const [grants, setGrants] = useState([]);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [editingGrantId, setEditingGrantId] = useState(null);
  const [editForm, setEditForm] = useState({});

  const fetchChartData = async () => {
    const response = await api.get("/dashboard/charts");
    setChartData(response.data);
  };

  const [filters, setFilters] = useState({
    principal_investigator: "",
    funding_agency: "",
    status: "",
  });

  const [form, setForm] = useState({
    title: "",
    principal_investigator: "",
    funding_agency: "",
    amount: "",
    deadline: "",
    status: "Pending",
    compliance_status: "",
  });

  const fetchGrants = async () => {
    const response = await api.get("/grants", {
      params: {
        principal_investigator: filters.principal_investigator || undefined,
        funding_agency: filters.funding_agency || undefined,
        status: filters.status || undefined,
      },
    });

    setGrants(response.data);
  };

  const fetchSummary = async () => {
    const response = await api.get("/dashboard/summary");
    setSummary(response.data);
  };

  useEffect(() => {
    fetchGrants();
    fetchSummary();
    fetchChartData();
  }, []);

  const handleFormChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const handleEditChange = (e) => {
    setEditForm({ ...editForm, [e.target.name]: e.target.value });
  };

  const startEdit = (grant) => {
    setEditingGrantId(grant.id);
    setEditForm({
      title: grant.title,
      principal_investigator: grant.principal_investigator,
      funding_agency: grant.funding_agency,
      amount: grant.amount,
      deadline: grant.deadline,
      status: grant.status,
      compliance_status: grant.compliance_status || "",
    });
  };

  const cancelEdit = () => {
    setEditingGrantId(null);
    setEditForm({});
  };

  const saveEdit = async (id) => {
    await api.put(`/grants/${id}`, {
      ...editForm,
      amount: Number(editForm.amount),
      compliance_status: editForm.compliance_status || null,
    });

    setEditingGrantId(null);
    setEditForm({});
    fetchGrants();
    fetchSummary();
    fetchChartData();
  };

  const handleCreateGrant = async (e) => {
    e.preventDefault();

    await api.post("/grants", {
      ...form,
      amount: Number(form.amount),
      compliance_status: form.compliance_status || null,
    });

    setForm({
      title: "",
      principal_investigator: "",
      funding_agency: "",
      amount: "",
      deadline: "",
      status: "Pending",
      compliance_status: "",
    });

    fetchGrants();
    fetchSummary();
    fetchChartData();
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchGrants();
  };

  const clearFilters = () => {
    setFilters({
      principal_investigator: "",
      funding_agency: "",
      status: "",
    });

    setTimeout(() => {
      fetchGrants();
    }, 0);
  };

  const deleteGrant = async (id) => {
    await api.delete(`/grants/${id}`);
    fetchGrants();
    fetchSummary();
    fetchChartData();
  };

  return (
    <div className="app">
      <h1>Research Grant Management Platform</h1>

      {summary && (
        <section className="summary-grid">
          <div className="summary-card">
            <p>Total Grants</p>
            <h2>{summary.total_grants}</h2>
          </div>

          <div className="summary-card">
            <p>Active Grants</p>
            <h2>{summary.active_grants}</h2>
          </div>

          <div className="summary-card">
            <p>Total Funding</p>
            <h2>${Number(summary.total_funding).toLocaleString()}</h2>
          </div>

          <div className="summary-card">
            <p>Missing Compliance</p>
            <h2>{summary.missing_compliance}</h2>
          </div>
        </section>
      )}

      {chartData && (
        <section className="charts-grid">

          <div className="card">
            <h2>Grants by Status</h2>

            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData.grants_by_status}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label
                >
                  {chartData.grants_by_status.map((entry, index) => (
                    <Cell key={index} />
                  ))}
                </Pie>

                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h2>Funding by Agency</h2>

            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData.funding_by_agency}>
                <XAxis dataKey="agency" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="funding" />
              </BarChart>
            </ResponsiveContainer>
          </div>

        </section>
      )}

      <section className="card">
        <h2>Create Grant</h2>

        <form onSubmit={handleCreateGrant} className="form">
          <input name="title" placeholder="Grant Title" value={form.title} onChange={handleFormChange} required />
          <input name="principal_investigator" placeholder="Principal Investigator" value={form.principal_investigator} onChange={handleFormChange} required />
          <input name="funding_agency" placeholder="Funding Agency" value={form.funding_agency} onChange={handleFormChange} required />
          <input name="amount" placeholder="Amount" type="number" value={form.amount} onChange={handleFormChange} required />
          <input name="deadline" type="date" value={form.deadline} onChange={handleFormChange} required />

          <select name="status" value={form.status} onChange={handleFormChange}>
            <option value="Pending">Pending</option>
            <option value="Active">Active</option>
            <option value="Completed">Completed</option>
            <option value="Urgent">Urgent</option>
          </select>

          <select name="compliance_status" value={form.compliance_status} onChange={handleFormChange}>
            <option value="">Missing</option>
            <option value="Complete">Complete</option>
            <option value="Incomplete">Incomplete</option>
            <option value="Under Review">Under Review</option>
          </select>

          <button type="submit">Add Grant</button>
        </form>
      </section>

      <section className="card">
        <h2>Search and Filter</h2>

        <form onSubmit={handleSearch} className="form">
          <input name="principal_investigator" placeholder="Search by PI" value={filters.principal_investigator} onChange={handleFilterChange} />
          <input name="funding_agency" placeholder="Search by Funding Agency" value={filters.funding_agency} onChange={handleFilterChange} />

          <select name="status" value={filters.status} onChange={handleFilterChange}>
            <option value="">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Active">Active</option>
            <option value="Completed">Completed</option>
            <option value="Urgent">Urgent</option>
          </select>

          <button type="submit">Apply Filters</button>
          <button type="button" className="secondary-button" onClick={clearFilters}>
            Clear Filters
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Grant Records</h2>

        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>PI</th>
              <th>Agency</th>
              <th>Amount</th>
              <th>Deadline</th>
              <th>Status</th>
              <th>Compliance</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {grants.map((grant) => (
              <tr key={grant.id}>
                {editingGrantId === grant.id ? (
                  <>
                    <td><input name="title" value={editForm.title} onChange={handleEditChange} /></td>
                    <td><input name="principal_investigator" value={editForm.principal_investigator} onChange={handleEditChange} /></td>
                    <td><input name="funding_agency" value={editForm.funding_agency} onChange={handleEditChange} /></td>
                    <td><input name="amount" type="number" value={editForm.amount} onChange={handleEditChange} /></td>
                    <td><input name="deadline" type="date" value={editForm.deadline} onChange={handleEditChange} /></td>
                    <td>
                      <select name="status" value={editForm.status} onChange={handleEditChange}>
                        <option value="Pending">Pending</option>
                        <option value="Active">Active</option>
                        <option value="Completed">Completed</option>
                        <option value="Urgent">Urgent</option>
                      </select>
                    </td>
                    <td>
                      <select name="compliance_status" value={editForm.compliance_status} onChange={handleEditChange}>
                        <option value="">Missing</option>
                        <option value="Complete">Complete</option>
                        <option value="Incomplete">Incomplete</option>
                        <option value="Under Review">Under Review</option>
                      </select>
                    </td>
                    <td>
                      <button type="button" onClick={() => saveEdit(grant.id)}>Save</button>
                      <button type="button" className="secondary-button" onClick={cancelEdit}>Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{grant.title}</td>
                    <td>{grant.principal_investigator}</td>
                    <td>{grant.funding_agency}</td>
                    <td>${Number(grant.amount).toLocaleString()}</td>
                    <td>{grant.deadline}</td>
                    <td>{grant.status}</td>
                    <td>{grant.compliance_status || "Missing"}</td>
                    <td>
                      <button type="button" onClick={() => startEdit(grant)}>Edit</button>
                      <button type="button" className="delete-button" onClick={() => deleteGrant(grant.id)}>
                        Delete
                      </button>
                    </td>
                  </>
                )}
              </tr>
            ))}

            {grants.length === 0 && (
              <tr>
                <td colSpan="8">No grants found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default App;