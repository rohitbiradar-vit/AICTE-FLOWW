import React, { useEffect, useState } from 'react';
import { apiRequest, downloadFile } from '../../api/client';
import { FolderCheck, UploadCloud, Download, ShieldCheck, AlertCircle, FileCheck } from 'lucide-react';

export const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  const handleDownload = async (docId: number, filename?: string) => {
    try {
      setDownloadingDocId(docId);
      await downloadFile(`/documents/${docId}/download`, filename);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloadingDocId(null);
    }
  };

  // Form states
  const [docType, setDocType] = useState('LAND_DEED');
  const [docTitle, setDocTitle] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const fetchDocuments = () => {
    setLoading(true);
    apiRequest<any[]>('/documents')
      .then((data) => setDocuments(data || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a file to upload.');
      return;
    }

    setUploadError('');
    setUploadSuccess('');
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('document_type', docType);
    if (docTitle) formData.append('title', docTitle);

    try {
      await apiRequest('/documents/upload', {
        method: 'POST',
        body: formData
      });
      setUploadSuccess('Document uploaded and ingested successfully! Scrutiny fields extracted.');
      setSelectedFile(null);
      setDocTitle('');
      fetchDocuments();
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex justify-between items-center">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-blue-700">Document Management Vault</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Statutory Institutional Repository</h1>
          <p className="text-xs text-slate-500 mt-1">
            Private server-controlled storage. Uploaded files are subjected to deterministic text extraction and validity rules.
          </p>
        </div>
        <div className="p-3 bg-blue-50 text-blue-800 rounded-xl">
          <FolderCheck className="w-6 h-6" />
        </div>
      </div>

      {/* Upload Box */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-blue-600" />
          Upload Statutory Document / Renewal Certificate
        </h3>

        {uploadError && <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">{uploadError}</div>}
        {uploadSuccess && <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg">{uploadSuccess}</div>}

        <form onSubmit={handleUploadSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Document Category</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
            >
              <option value="LAND_DEED">Land Title Deed / 99-Year Lease</option>
              <option value="BUILDING_PLAN">Sanctioned Building Blueprint</option>
              <option value="FIRE_SAFETY_CERT">Fire Safety Certificate (NOC)</option>
              <option value="NOC_AFFILIATING_UNIVERSITY">University Affiliation NOC</option>
              <option value="FACULTY_LIST">Statutory Faculty Cadre Roster</option>
              <option value="OCCUPANCY_CERTIFICATE">Municipal Occupancy Certificate</option>
              <option value="AUDITED_FINANCIALS">Audited Balance Sheet</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Custom Title / Remark</label>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="e.g. Land Deed 2026 Renewal"
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Select File (PDF, PNG, JPG)</label>
            <input
              type="file"
              accept=".pdf,.png,.jpeg,.jpg"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs p-1.5 border border-slate-300 rounded-lg bg-slate-50 cursor-pointer"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={isUploading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-md cursor-pointer flex items-center justify-center gap-1.5"
            >
              <UploadCloud className="w-4 h-4" />
              <span>{isUploading ? 'Ingesting...' : 'Upload & Extract'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex justify-between items-center">
          <h3 className="font-bold text-sm text-slate-900">Current Documents Vault ({documents.length})</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3.5">Document Title</th>
                <th className="p-3.5">Category</th>
                <th className="p-3.5">Version</th>
                <th className="p-3.5">Issue Date</th>
                <th className="p-3.5">Expiry Date</th>
                <th className="p-3.5">Verification</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={7} className="p-6 text-center text-slate-400">Loading documents...</td></tr>
              ) : documents.length === 0 ? (
                <tr><td colSpan={7} className="p-6 text-center text-slate-400">No documents uploaded yet.</td></tr>
              ) : (
                documents.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-3.5">
                      <div className="font-semibold text-slate-900">{d.title}</div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">{d.original_filename}</div>
                    </td>
                    <td className="p-3.5 font-mono text-slate-600">{d.document_type}</td>
                    <td className="p-3.5 font-mono font-bold text-blue-700">v{d.version}</td>
                    <td className="p-3.5 font-mono text-slate-600">{d.issue_date ? new Date(d.issue_date).toLocaleDateString() : 'N/A'}</td>
                    <td className="p-3.5 font-mono text-slate-600">{d.expiry_date ? new Date(d.expiry_date).toLocaleDateString() : 'Permanent'}</td>
                    <td className="p-3.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        d.verification_status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800' :
                        d.verification_status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                        d.verification_status === 'REQUIRES_CLARIFICATION' ? 'bg-amber-100 text-amber-800' :
                        'bg-slate-100 text-slate-800'
                      }`}>
                        {d.verification_status}
                      </span>
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        type="button"
                        onClick={() => handleDownload(d.id, d.original_filename)}
                        disabled={downloadingDocId === d.id}
                        className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-semibold inline-flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <Download className="w-3.5 h-3.5" /> {downloadingDocId === d.id ? 'Downloading...' : 'Download'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
