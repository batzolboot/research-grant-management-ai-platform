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

function Dashboard({ user }) {
  const isAdmin = user.role === "Admin";
  const [grants, setGrants] = useState([]);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedGrantId, setSelectedGrantId] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [extractedDocument, setExtractedDocument] = useState(null);
  const [aiResult, setAiResult] = useState(null);
  const [aiMessage, setAiMessage] = useState("");
  const [extractionMessage, setExtractionMessage] = useState("");
  const [editingGrantId, setEditingGrantId] = useState(null);
  const [editForm, setEditForm] = useState({});

  const fetchChartData = async () => {
    const response = await api.get("/dashboard/charts");
    setChartData(response.data);
  };

  const fetchDocuments = async () => {
    const response = await api.get("/documents");
    setDocuments(response.data);
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
    fetchDocuments();
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

  const handleAiExtract = async (documentId) => {
    setAiMessage("AI is extracting grant fields...");
    setAiResult(null);

    try {
      const response = await api.post(
        `/documents/${documentId}/ai-extract`
      );

      setAiResult(response.data);
      setAiMessage("");
    } catch (error) {
      setAiMessage(
        error.response?.data?.detail || "AI extraction failed."
      );
    }
  };

  const handleExtractText = async (documentId) => {
    setExtractionMessage("Extracting text...");

    try {
      const response = await api.get(
        `/documents/${documentId}/extract`
      );

      setExtractedDocument(response.data);
      setExtractionMessage("");
    } catch (error) {
      setExtractedDocument(null);
      setExtractionMessage(
        error.response?.data?.detail || "Text extraction failed."
      );
    }
  };

  const handleDocumentUpload = async (e) => {
    e.preventDefault();
    setUploadMessage("");

    if (!selectedGrantId || !selectedFile) {
      setUploadMessage("Choose a grant and a file.");
      return;
  }

  const formData = new FormData();
  formData.append("grant_id", selectedGrantId);
  formData.append("file", selectedFile);

  try {
    await api.post("/documents/upload", formData);

    setSelectedGrantId("");
    setSelectedFile(null);
    setUploadMessage("Document uploaded successfully.");

    e.target.reset();
    fetchDocuments();
  } catch (error) {
    setUploadMessage(
      error.response?.data?.detail || "Document upload failed."
    );
  }
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
      {isAdmin && (
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
      )}

      {isAdmin && (
        <section className="card">
          <h2>Upload Grant Document</h2>

          <form onSubmit={handleDocumentUpload} className="form">
            <select
              value={selectedGrantId}
              onChange={(e) => setSelectedGrantId(e.target.value)}
              required
            >
              <option value="">Select a grant</option>

              {grants.map((grant) => (
                <option key={grant.id} value={grant.id}>
                  ID {grant.id} — {grant.title}
                </option>
              ))}
            </select>

            <input
              type="file"
              accept=".pdf,.csv,.xlsx,.xls"
              onChange={(e) => setSelectedFile(e.target.files[0])}
              required
            />

            <button type="submit">
              Upload Document
            </button>
          </form>

          {uploadMessage && (
            <p className="upload-message">{uploadMessage}</p>
          )}
        </section>
      )}

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
              <th>ID</th>
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
                    <td>{grant.id}</td>
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
                    <td>{grant.id}</td>
                    <td>{grant.title}</td>
                    <td>{grant.principal_investigator}</td>
                    <td>{grant.funding_agency}</td>
                    <td>${Number(grant.amount).toLocaleString()}</td>
                    <td>{grant.deadline}</td>
                    <td>{grant.status}</td>
                    <td>{grant.compliance_status || "Missing"}</td>
                    <td>
                      {isAdmin ? (
                        <>
                          <button
                            type="button"
                            onClick={() => startEdit(grant)}
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            className="delete-button"
                            onClick={() => deleteGrant(grant.id)}
                          >
                            Delete
                          </button>
                        </>
                      ) : (
                        <span>View only</span>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}

            {grants.length === 0 && (
              <tr>
                <td colSpan="9">No grants found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h2>Recent Documents</h2>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Filename</th>
              <th>Grant ID</th>
              <th>File Type</th>
              <th>Uploaded By</th>
              <th>Uploaded At</th>
              <th>Text</th>
              <th>AI</th>
            </tr>
          </thead>

          <tbody>
            {documents.map((uploadedDocument) => (
              <tr key={uploadedDocument.id}>
                <td>{uploadedDocument.id}</td>
                <td>
                  <button
                    type="button"
                    className="document-link"
                    onClick={async () => {
                      const response = await api.get(
                        `/documents/${uploadedDocument.id}/file`,
                        {
                          responseType: "blob",
                        }
                      );

                      const fileUrl = window.URL.createObjectURL(
                        new Blob([response.data])
                      );

                      const link = window.document.createElement("a");
                      link.href = fileUrl;
                      link.download = uploadedDocument.original_filename;

                      window.document.body.appendChild(link);
                      link.click();
                      link.remove();

                      window.URL.revokeObjectURL(fileUrl);
                    }}
                  >
                    {uploadedDocument.original_filename}
                  </button>
                </td>
                <td>{uploadedDocument.grant_id}</td>
                <td>{uploadedDocument.file_type}</td>
                <td>{uploadedDocument.uploaded_by}</td>
                <td>
                  {new Date(uploadedDocument.uploaded_at).toLocaleString()}
                </td>
                <td>
                  <button
                    type="button"
                    onClick={() => handleExtractText(uploadedDocument.id)}
                  >
                    Extract Text
                  </button>
                </td>
                <td>
                  {isAdmin ? (
                    <button
                      type="button"
                      onClick={() => handleAiExtract(uploadedDocument.id)}
                    >
                      AI Extract
                    </button>
                  ) : (
                    <span>Admin only</span>
                  )}
                </td>
              </tr>
            ))}

            {documents.length === 0 && (
              <tr>
                <td colSpan="8">No documents uploaded.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h2>Extracted Text Preview</h2>

        {extractionMessage && (
          <p>{extractionMessage}</p>
        )}

        {extractedDocument ? (
          <>
            <p>
              <strong>Filename:</strong>{" "}
              {extractedDocument.filename}
            </p>

            <p>
              <strong>Characters:</strong>{" "}
              {extractedDocument.character_count}
            </p>

            <pre className="text-preview">
              {extractedDocument.text}
            </pre>
          </>
        ) : (
          <p>Select “Extract Text” beside a document.</p>
        )}
      </section>

      <section className="card">
        <h2>AI Extraction Review</h2>

        {aiMessage && <p>{aiMessage}</p>}

        {aiResult ? (
          <div className="form">
            <input
              name="title"
              placeholder="Grant Title"
              value={aiResult.title || ""}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  title: e.target.value,
                })
              }
            />

            <input
              name="principal_investigator"
              placeholder="Principal Investigator"
              value={aiResult.principal_investigator || ""}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  principal_investigator: e.target.value,
                })
              }
            />

            <input
              name="funding_agency"
              placeholder="Funding Agency"
              value={aiResult.funding_agency || ""}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  funding_agency: e.target.value,
                })
              }
            />

            <input
              name="amount"
              type="number"
              placeholder="Amount"
              value={aiResult.amount || ""}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  amount: e.target.value,
                })
              }
            />

            <input
              name="deadline"
              type="date"
              value={aiResult.deadline || ""}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  deadline: e.target.value,
                })
              }
            />

            <select
              name="status"
              value={aiResult.status || "Pending"}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  status: e.target.value,
                })
              }
            >
              <option value="Pending">Pending</option>
              <option value="Active">Active</option>
              <option value="Completed">Completed</option>
              <option value="Urgent">Urgent</option>
            </select>

            <select
              name="compliance_status"
              value={aiResult.compliance_status || ""}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  compliance_status: e.target.value,
                })
              }
            >
              <option value="">Missing</option>
              <option value="Complete">Complete</option>
              <option value="Incomplete">Incomplete</option>
              <option value="Under Review">Under Review</option>
            </select>

            <textarea
              name="summary"
              placeholder="Summary"
              value={aiResult.summary || ""}
              onChange={(e) =>
                setAiResult({
                  ...aiResult,
                  summary: e.target.value,
                })
              }
            />

            <button
              type="button"
              onClick={() => {
                setForm({
                  title: aiResult.title || "",
                  principal_investigator:
                    aiResult.principal_investigator || "",
                  funding_agency: aiResult.funding_agency || "",
                  amount: aiResult.amount || "",
                  deadline: aiResult.deadline || "",
                  status: aiResult.status || "Pending",
                  compliance_status:
                    aiResult.compliance_status || "",
                });

                window.scrollTo({
                  top: 0,
                  behavior: "smooth",
                });
              }}
            >
              Use These Fields
            </button>
          </div>
        ) : (
          <p>Select “AI Extract” beside a document.</p>
        )}
      </section>
    </div>
  );
}

export default Dashboard;