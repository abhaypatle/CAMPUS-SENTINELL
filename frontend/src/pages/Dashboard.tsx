
import React, { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'

type IncidentStatus =
  | 'OPEN'
  | 'IN_PROGRESS'
  | 'RESOLVED'

type IncidentReport = {
  id: string
  reporter_id: string
  title: string
  description: string
  category: string
  severity: string
  location_text?: string | null
  status: IncidentStatus
  created_at?: string | null
  updated_at?: string | null
}

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth()

  const [reports, setReports] = useState<IncidentReport[]>([])
  const [loadingReports, setLoadingReports] = useState(false)

  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('SAFETY')
  const [severity, setSeverity] = useState('LOW')
  const [location, setLocation] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [updatingReportId, setUpdatingReportId] = useState<string | null>(
    null,
  )

  const loadReports = useCallback(async () => {
    setLoadingReports(true)
    setError(null)

    try {
      const data = await api.get('/api/v1/reports', true)
      setReports(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load reports')
    } finally {
      setLoadingReports(false)
    }
  }, [])

  useEffect(() => {
    if (user) {
      loadReports()
    }
  }, [user, loadReports])

  const submitReport = async (e: React.FormEvent) => {
    e.preventDefault()

    setSubmitting(true)
    setSuccess(null)
    setError(null)

    try {
      await api.post(
        '/api/v1/reports',
        {
          title,
          description,
          category,
          severity,
          location_text: location || null,
        },
        true,
      )

      setTitle('')
      setDescription('')
      setCategory('SAFETY')
      setSeverity('LOW')
      setLocation('')

      setSuccess(
        'Incident report submitted successfully.',
      )

      await loadReports()
    } catch (err: any) {
      setError(
        err.message || 'Failed to submit incident',
      )
    } finally {
      setSubmitting(false)
    }
  }

  const updateStatus = async (
    reportId: string,
    newStatus: IncidentStatus,
  ) => {
    setUpdatingReportId(reportId)
    setError(null)
    setSuccess(null)

    try {
      await api.patch(
        `/api/v1/reports/${reportId}/status`,
        {
          status: newStatus,
        },
        true,
      )

      setSuccess('Report status updated successfully.')

      await loadReports()
    } catch (err: any) {
      setError(
        err.message || 'Failed to update status',
      )
    } finally {
      setUpdatingReportId(null)
    }
  }

  if (!user) {
    return null
  }

  const canUpdateStatus =
    user.role === 'RESPONDER' ||
    user.role === 'ADMIN'

  return (
    <div className="container">
      <header>
        <h1>Campus Sentinel</h1>

        <button
          type="button"
          onClick={logout}
        >
          Logout
        </button>
      </header>

      <main>
        <section>
          <h2>Dashboard</h2>

          <p>
            Welcome, <strong>{user.name}</strong>
          </p>

          <p>
            Email: {user.email}
          </p>

          <p>
            Role: {user.role}
          </p>
        </section>

        <hr />

        {user.role === 'REPORTER' && (
          <section>
            <h2>Report an Incident</h2>

            <form onSubmit={submitReport}>
              <div>
                <label htmlFor="title">
                  Title
                </label>

                <input
                  id="title"
                  type="text"
                  value={title}
                  onChange={(e) =>
                    setTitle(e.target.value)
                  }
                  minLength={3}
                  maxLength={200}
                  required
                />
              </div>

              <div>
                <label htmlFor="description">
                  Description
                </label>

                <textarea
                  id="description"
                  value={description}
                  onChange={(e) =>
                    setDescription(e.target.value)
                  }
                  minLength={3}
                  maxLength={2000}
                  required
                  rows={5}
                />
              </div>

              <div>
                <label htmlFor="category">
                  Category
                </label>

                <select
                  id="category"
                  value={category}
                  onChange={(e) =>
                    setCategory(e.target.value)
                  }
                >
                  <option value="SAFETY">
                    Safety
                  </option>

                  <option value="FIRE">
                    Fire
                  </option>

                  <option value="MEDICAL">
                    Medical
                  </option>

                  <option value="SECURITY">
                    Security
                  </option>

                  <option value="INFRASTRUCTURE">
                    Infrastructure
                  </option>

                  <option value="OTHER">
                    Other
                  </option>
                </select>
              </div>

              <div>
                <label htmlFor="severity">
                  Severity
                </label>

                <select
                  id="severity"
                  value={severity}
                  onChange={(e) =>
                    setSeverity(e.target.value)
                  }
                >
                  <option value="LOW">
                    Low
                  </option>

                  <option value="MEDIUM">
                    Medium
                  </option>

                  <option value="HIGH">
                    High
                  </option>

                  <option value="CRITICAL">
                    Critical
                  </option>
                </select>
              </div>

              <div>
                <label htmlFor="location">
                  Location
                </label>

                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) =>
                    setLocation(e.target.value)
                  }
                  maxLength={255}
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
              >
                {submitting
                  ? 'Submitting...'
                  : 'Submit Incident'}
              </button>
            </form>
          </section>
        )}

        {success && (
          <p role="status">
            {success}
          </p>
        )}

        {error && (
          <p role="alert">
            {error}
          </p>
        )}

        <hr />

        <section>
          <div>
            <h2>Incident Reports</h2>

            <button
              type="button"
              onClick={loadReports}
              disabled={loadingReports}
            >
              {loadingReports
                ? 'Refreshing...'
                : 'Refresh Reports'}
            </button>
          </div>

          {loadingReports &&
            reports.length === 0 && (
              <p>Loading reports...</p>
            )}

          {!loadingReports &&
            reports.length === 0 && (
              <p>No reports found.</p>
            )}

          {reports.length > 0 && (
            <div>
              {reports.map((report) => (
                <article key={report.id}>
                  <h3>{report.title}</h3>

                  <p>
                    <strong>Status:</strong>{' '}
                    {report.status}
                  </p>

                  <p>
                    <strong>Category:</strong>{' '}
                    {report.category}
                  </p>

                  <p>
                    <strong>Severity:</strong>{' '}
                    {report.severity}
                  </p>

                  <p>
                    <strong>Location:</strong>{' '}
                    {report.location_text ||
                      'Not specified'}
                  </p>

                  <p>
                    <strong>Description:</strong>{' '}
                    {report.description}
                  </p>

                  <small>
                    Report ID: {report.id}
                  </small>

                  {canUpdateStatus && (
                    <div>
                      <label
                        htmlFor={`status-${report.id}`}
                      >
                        Update status
                      </label>

                      <select
                        id={`status-${report.id}`}
                        value={report.status}
                        disabled={
                          updatingReportId ===
                          report.id
                        }
                        onChange={(e) =>
                          updateStatus(
                            report.id,
                            e.target.value as IncidentStatus,
                          )
                        }
                      >
                        <option value="OPEN">
                          Open
                        </option>

                        <option value="IN_PROGRESS">
                          In Progress
                        </option>

                        <option value="RESOLVED">
                          Resolved
                        </option>
                      </select>
                    </div>
                  )}

                  <hr />
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default Dashboard
