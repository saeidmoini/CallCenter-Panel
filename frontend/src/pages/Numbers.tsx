import { FormEvent, useEffect, useMemo, useState } from 'react'
import client from '../api/client'
import dayjs from 'dayjs'

interface PhoneNumber {
  id: number
  phone_number: string
  status: string
  total_attempts: number
  last_attempt_at?: string
  last_status_change_at?: string
}

const statusLabels: Record<string, string> = {
  IN_QUEUE: 'در صف تماس',
  MISSED: 'از دست رفته',
  CONNECTED: 'موفق',
  FAILED: 'خطا دریافت شد',
  NOT_INTERESTED: 'عدم نیاز کاربر',
  HANGUP: 'قطع تماس توسط کاربر',
  DISCONNECTED: 'ناموفق',
}

const statusColors: Record<string, string> = {
  IN_QUEUE: 'bg-amber-100 text-amber-800',
  MISSED: 'bg-orange-100 text-orange-800',
  CONNECTED: 'bg-emerald-100 text-emerald-800',
  FAILED: 'bg-red-100 text-red-800',
  NOT_INTERESTED: 'bg-slate-200 text-slate-800',
  HANGUP: 'bg-purple-100 text-purple-800',
  DISCONNECTED: 'bg-gray-200 text-gray-800',
}

const NumbersPage = () => {
  const [numbers, setNumbers] = useState<PhoneNumber[]>([])
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [search, setSearch] = useState('')
  const [newNumbers, setNewNumbers] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const pageSize = 50
  const [hasMore, setHasMore] = useState(false)
  const [totalCount, setTotalCount] = useState(0)

  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [excludedIds, setExcludedIds] = useState<Set<number>>(new Set())
  const [selectAll, setSelectAll] = useState(false)

  const [bulkAction, setBulkAction] = useState<'update_status' | 'reset' | 'delete'>('update_status')
  const [bulkStatus, setBulkStatus] = useState<string>('IN_QUEUE')

  const fetchNumbers = async () => {
    setLoading(true)
    const { data } = await client.get<PhoneNumber[]>('/api/numbers', {
      params: {
        status: statusFilter || undefined,
        search: search || undefined,
        skip: page * pageSize,
        limit: pageSize,
      },
    })
    setNumbers(data)
    setHasMore(data.length === pageSize)
    setLoading(false)
  }

  const fetchStats = async () => {
    const { data } = await client.get<{ total: number }>('/api/numbers/stats', {
      params: {
        status: statusFilter || undefined,
        search: search || undefined,
      },
    })
    setTotalCount(data.total)
  }

  useEffect(() => {
    fetchNumbers()
    fetchStats()
  }, [page, statusFilter, search])

  const clearSelection = () => {
    setSelectedIds(new Set())
    setExcludedIds(new Set())
    setSelectAll(false)
  }

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault()
    const phone_numbers = newNumbers.split(/\n|,/).map((s) => s.trim()).filter(Boolean)
    if (!phone_numbers.length) return
    await client.post('/api/numbers', { phone_numbers })
    setNewNumbers('')
    fetchNumbers()
    fetchStats()
  }

  const updateStatus = async (id: number, status: string) => {
    await client.put(`/api/numbers/${id}/status`, { status })
    fetchNumbers()
  }

  const deleteNumber = async (id: number) => {
    const ok = window.confirm('این شماره حذف شود؟')
    if (!ok) return
    await client.delete(`/api/numbers/${id}`)
    setNumbers((prev) => prev.filter((n) => n.id !== id))
    setSelectedIds((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    setExcludedIds((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    fetchStats()
  }

  const resetNumber = async (id: number) => {
    await client.post(`/api/numbers/${id}/reset`)
    fetchNumbers()
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadMessage(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await client.post('/api/numbers/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setUploadMessage(`افزودن از فایل: ${data.inserted} اضافه شد، ${data.duplicates} تکراری، ${data.invalid} نامعتبر`)
      fetchNumbers()
    } catch (err) {
      setUploadMessage('خطا در بارگذاری فایل')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const isRowSelected = (id: number) => {
    if (selectAll) {
      return !excludedIds.has(id)
    }
    return selectedIds.has(id)
  }

  const toggleRow = (id: number) => {
    if (selectAll) {
      const next = new Set(excludedIds)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      setExcludedIds(next)
    } else {
      const next = new Set(selectedIds)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      setSelectedIds(next)
    }
  }

  const allVisibleSelected = useMemo(
    () => numbers.length > 0 && numbers.every((n) => isRowSelected(n.id)),
    [numbers, selectedIds, excludedIds, selectAll],
  )

  const toggleCurrentPage = () => {
    if (selectAll) {
      const next = new Set(excludedIds)
      numbers.forEach((n) => {
        if (allVisibleSelected) {
          next.add(n.id)
        } else {
          next.delete(n.id)
        }
      })
      setExcludedIds(next)
    } else {
      const next = new Set(selectedIds)
      numbers.forEach((n) => {
        if (allVisibleSelected) {
          next.delete(n.id)
        } else {
          next.add(n.id)
        }
      })
      setSelectedIds(next)
    }
  }

  const handleBulk = async () => {
    const ids = selectAll ? [] : Array.from(selectedIds)
    const excluded_ids = selectAll ? Array.from(excludedIds) : []
    if (!selectAll && ids.length === 0) {
      alert('هیچ ردیفی انتخاب نشده است')
      return
    }
    if (bulkAction === 'delete') {
      const ok = window.confirm('حذف دسته‌جمعی انجام شود؟')
      if (!ok) return
    }
    const payload: any = {
      action: bulkAction,
      ids,
      select_all: selectAll,
      excluded_ids,
      filter_status: statusFilter || undefined,
      search: search || undefined,
    }
    if (bulkAction === 'update_status') {
      payload.status = bulkStatus
    }
    await client.post('/api/numbers/bulk', payload)
    clearSelection()
    fetchNumbers()
    fetchStats()
  }

  const selectedCount = selectAll ? totalCount - excludedIds.size : selectedIds.size

  return (
    <div className="space-y-6 px-2 md:px-0 max-w-full w-full min-w-0">
      <div className="bg-white rounded-xl border border-slate-100 p-4 shadow-sm w-full min-w-0">
        <h2 className="font-semibold mb-3">افزودن شماره جدید</h2>
        <div className="flex flex-col gap-6">
          <div className="flex-1 space-y-2 w-full">
            <label className="block text-sm font-medium text-slate-700">افزودن از فایل (یک ستون شماره)</label>
            <input
              type="file"
              accept=".csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              onChange={handleUpload}
              className="block w-full text-sm text-slate-700 file:mr-4 file:rounded file:border-0 file:bg-brand-500 file:px-4 file:py-2 file:text-white hover:file:bg-brand-700"
              disabled={uploading}
            />
            {uploadMessage && <div className="text-xs text-slate-600">{uploadMessage}</div>}
          </div>
          <form className="flex-1 space-y-3 w-full" onSubmit={handleAdd}>
            <textarea
              className="w-full rounded border border-slate-200 px-3 py-2 text-sm"
              rows={3}
              placeholder="هر خط یک شماره"
              value={newNumbers}
              onChange={(e) => setNewNumbers(e.target.value)}
            />
            <button type="submit" className="rounded bg-brand-500 text-white px-4 py-2 text-sm hover:bg-brand-700">
              افزودن به صف
            </button>
          </form>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 p-4 shadow-sm w-full min-w-0">
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <select
            className="rounded border border-slate-200 px-2 py-1 text-sm"
            value={statusFilter}
            onChange={(e) => {
              setPage(0)
              clearSelection()
              setStatusFilter(e.target.value)
            }}
          >
            <option value="">همه وضعیت‌ها</option>
            {Object.entries(statusLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
          <input
            value={search}
            onChange={(e) => {
              setPage(0)
              clearSelection()
              setSearch(e.target.value)
            }}
            placeholder="جستجوی شماره"
            className="rounded border border-slate-200 px-2 py-1 text-sm"
          />
          <button onClick={() => { setPage(0); fetchNumbers(); fetchStats(); }} className="rounded bg-slate-900 text-white px-3 py-1 text-sm">
            بروزرسانی
          </button>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span>انتخاب شده: {selectedCount}</span>
            <button
              className="rounded border border-slate-200 px-2 py-1 text-[11px]"
              onClick={() => {
                setSelectAll(true)
                setSelectedIds(new Set())
                setExcludedIds(new Set())
              }}
              disabled={totalCount === 0}
            >
              انتخاب همه نتایج
            </button>
            <button
              className="rounded border border-slate-200 px-2 py-1 text-[11px]"
              onClick={clearSelection}
              disabled={selectedCount === 0 && !selectAll}
            >
              لغو انتخاب
            </button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-600">عملیات گروهی</label>
            <select
              className="rounded border border-slate-200 px-2 py-1 text-sm"
              value={bulkAction}
              onChange={(e) => setBulkAction(e.target.value as any)}
            >
              <option value="update_status">تغییر وضعیت</option>
              <option value="reset">ریست (برگشت به صف)</option>
              <option value="delete">حذف</option>
            </select>
            {bulkAction === 'update_status' && (
              <select
                className="rounded border border-slate-200 px-2 py-1 text-sm"
                value={bulkStatus}
                onChange={(e) => setBulkStatus(e.target.value)}
              >
                {Object.entries(statusLabels).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            )}
            <button
              className="rounded bg-brand-500 text-white px-3 py-1 text-sm disabled:opacity-50"
              disabled={selectedCount === 0}
              onClick={handleBulk}
            >
              اعمال
            </button>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <span className="text-xs text-slate-600">صفحه {page + 1}</span>
            <button
              className="text-xs rounded border border-slate-200 px-2 py-1 disabled:opacity-50"
              onClick={() => setPage((p) => Math.max(p - 1, 0))}
              disabled={page === 0}
            >
              قبلی
            </button>
            <button
              className="text-xs rounded border border-slate-200 px-2 py-1 disabled:opacity-50"
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
            >
              بعدی
            </button>
          </div>
        </div>
        {loading ? (
          <div className="text-sm">در حال بارگذاری...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px] text-sm text-right whitespace-nowrap">
              <thead>
                <tr className="text-slate-500">
                  <th className="py-2 text-right w-10">
                    <input type="checkbox" checked={allVisibleSelected} onChange={toggleCurrentPage} />
                  </th>
                  <th className="py-2 text-right">شماره</th>
                  <th className="text-right">وضعیت</th>
                  <th className="text-right">تعداد تلاش</th>
                  <th className="text-right w-32">آخرین تلاش</th>
                  <th className="text-right w-80">اقدامات</th>
                </tr>
              </thead>
              <tbody>
                {numbers.map((n) => (
                  <tr key={n.id} className="border-t">
                    <td className="py-2 text-right">
                      <input type="checkbox" checked={isRowSelected(n.id)} onChange={() => toggleRow(n.id)} />
                    </td>
                    <td className="py-2 font-mono text-xs">{n.phone_number}</td>
                    <td className="text-right">
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${statusColors[n.status] || 'bg-slate-100 text-slate-700'}`}
                      >
                        {statusLabels[n.status] || n.status}
                      </span>
                    </td>
                    <td className="text-right">{n.total_attempts}</td>
                    <td className="text-right">
                      {n.last_attempt_at ? dayjs(n.last_attempt_at).calendar('jalali').format('YYYY/MM/DD HH:mm') : '-'}
                    </td>
                    <td className="text-right w-80">
                      <div className="flex items-center justify-start gap-4">
                        <select
                          className="rounded border border-slate-200 px-2 py-1 text-xs w-40"
                          value={n.status}
                          onChange={(e) => updateStatus(n.id, e.target.value)}
                        >
                          {Object.keys(statusLabels).map((key) => (
                            <option key={key} value={key}>
                              {statusLabels[key]}
                            </option>
                          ))}
                        </select>
                        <button
                          className="text-xs text-amber-700 ml-2"
                          onClick={() => resetNumber(n.id)}
                          title="بازگشت به صف"
                        >
                          ریست
                        </button>
                        <button
                          className="text-xs text-red-600"
                          onClick={() => deleteNumber(n.id)}
                          title="حذف شماره"
                        >
                          حذف
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default NumbersPage
