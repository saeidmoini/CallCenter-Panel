import { useEffect, useState } from 'react'
import client from '../api/client'

interface ScheduleConfig {
  enabled: boolean
  version: number
}

const DashboardPage = () => {
  const [config, setConfig] = useState<ScheduleConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const fetchConfig = async () => {
    setLoading(true)
    const { data } = await client.get<ScheduleConfig>('/api/schedule')
    setConfig(data)
    setLoading(false)
  }

  useEffect(() => {
    fetchConfig()
  }, [])

  const toggleDialer = async () => {
    if (!config) return
    setSaving(true)
    try {
      const { data } = await client.put('/api/schedule', { enabled: !config.enabled })
      setConfig((prev) => (prev ? { ...prev, enabled: data.enabled } : data))
    } finally {
      setSaving(false)
    }
  }

  const statusBadge = (on: boolean) => (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${on ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
      {on ? 'فعال' : 'غیرفعال'}
    </span>
  )

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="bg-white rounded-xl shadow-sm p-4 border border-slate-100 flex flex-col gap-2">
        <div className="text-sm text-slate-500">وضعیت کلی پنل</div>
        <div className="flex items-center gap-3">
          {statusBadge(!!config?.enabled)}
          <span className="text-sm text-slate-600">ارسال شماره به سرور تماس</span>
        </div>
        <div className="text-xs text-slate-500">نسخه زمان‌بندی: {config?.version ?? '-'}</div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4 border border-slate-100 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-500">مرکز تماس</div>
          {statusBadge(!!config?.enabled)}
        </div>
        <div className="text-sm text-slate-700">
          کنترل روشن/خاموش بودن سرور مرکز تماس. در صورت خاموش بودن هیچ شماره‌ای ارسال نمی‌شود.
        </div>
        <button
          className="rounded bg-brand-500 text-white px-4 py-2 text-sm disabled:opacity-50"
          onClick={toggleDialer}
          disabled={saving || loading}
        >
          {saving ? 'در حال اعمال...' : config?.enabled ? 'خاموش کردن' : 'روشن کردن'}
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4 border border-slate-100">
        <div className="text-sm text-slate-500">نکته</div>
        <div className="text-sm">نمایش تاریخ در رابط کاربری به‌صورت تقویم شمسی است.</div>
      </div>
    </div>
  )
}

export default DashboardPage
