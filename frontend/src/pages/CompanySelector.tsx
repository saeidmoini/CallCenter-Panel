import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

interface Company {
  id: number
  name: string
  display_name: string
  is_active: boolean
}

const CompanySelectorPage = () => {
  const navigate = useNavigate()
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const { data } = await client.get<Company[]>('/api/companies')
        setCompanies(data.filter(c => c.is_active))
      } catch (error) {
        console.error('Failed to fetch companies', error)
      } finally {
        setLoading(false)
      }
    }

    fetchCompanies()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-500">در حال بارگذاری...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">انتخاب شرکت</h1>
        <p className="text-sm text-slate-600 mt-1">
          برای مدیریت پنل یک شرکت را انتخاب کنید
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {companies.map((company) => (
          <div
            key={company.id}
            className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
            onClick={() => navigate(`/${company.name}/dashboard`)}
          >
            <div className="flex flex-col items-center text-center gap-3">
              <div className="w-16 h-16 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 text-2xl font-bold">
                {company.display_name.charAt(0)}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                  {company.display_name}
                </h2>
                <p className="text-sm text-slate-500 font-mono">{company.name}</p>
              </div>
              <div className="mt-2">
                <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                  فعال
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {companies.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <p className="text-slate-500">هیچ شرکتی یافت نشد</p>
        </div>
      )}
    </div>
  )
}

export default CompanySelectorPage
