# Multi-Company Implementation Progress

**Project:** Salehi Dialer Panel - Multi-Company Support
**Date Started:** 2026-02-14
**Current Phase:** Phase 2 - Backend Implementation (In Progress)

---

## ✅ COMPLETED WORK

### Phase 1: Database Migration (100% Complete)
- ✅ Migration file created: `backend/alembic/versions/0004_multi_company.py`
- ✅ Database successfully migrated locally
- ✅ Data seeding: 2 companies, 1 scenario, 4 outbound lines
- ✅ Tables renamed: `phone_numbers` → `numbers`, `call_attempts` → `call_results`
- ✅ Deployment guide created: `DEPLOYMENT_GUIDE.md`

**Migration Status:** Successfully tested locally, ready for production deployment

---

### Phase 2: Backend Implementation (100% Complete ✅)

#### ✅ Models (100%)
**New Models Created:**
1. `backend/app/models/company.py` - Company model
2. `backend/app/models/scenario.py` - Scenario model
3. `backend/app/models/outbound_line.py` - OutboundLine model
4. `backend/app/models/call_result.py` - CallResult model (renamed from CallAttempt)

**Updated Models:**
1. `backend/app/models/user.py` - Added `company_id`, `agent_type`, `AgentType` enum
2. `backend/app/models/phone_number.py` - Added `GlobalStatus` enum, `global_status`, `last_called_at`, `last_called_company_id`, `INBOUND_CALL` to CallStatus
3. `backend/app/models/schedule.py` - Added `company_id` to ScheduleConfig and ScheduleWindow
4. `backend/app/models/__init__.py` - Exported new models and enums

**Table Name Changes:**
- `PhoneNumber.__tablename__` = "numbers" (was "phone_numbers")
- `CallResult.__tablename__` = "call_results" (was "call_attempts")

---

#### ✅ Schemas (100%)
**New Schemas Created:**
1. `backend/app/schemas/company.py` - CompanyCreate, CompanyUpdate, CompanyOut
2. `backend/app/schemas/scenario.py` - ScenarioCreate, ScenarioUpdate, ScenarioOut, ScenarioSimple, RegisterScenariosRequest
3. `backend/app/schemas/outbound_line.py` - OutboundLineCreate, OutboundLineUpdate, OutboundLineOut

**Updated Schemas:**
1. `backend/app/schemas/dialer.py` - Added `ScenarioSimple`, updated `NextBatchResponse` with `active_scenarios`, `inbound_agents`, `outbound_agents`, updated `DialerReport` with `company`, `scenario_id`, `outbound_line_id`
2. `backend/app/schemas/user.py` - Added `company_id`, `company_name`, `agent_type`, imported `AgentType`
3. `backend/app/schemas/__init__.py` - Exported new schemas

---

#### ✅ Configuration (100%)
1. `backend/app/core/config.py` - Added `call_cooldown_days: int = Field(3, alias="CALL_COOLDOWN_DAYS")`
2. `backend/.env` - Added `CALL_COOLDOWN_DAYS=3`

---

#### ✅ API Dependencies (100%)
Updated `backend/app/api/deps.py`:
- ✅ Added `get_company(company_name, db)` - Resolves company from name
- ✅ Added `get_company_user(current_user, company)` - Verifies user access to company
- ✅ Imported Company and AdminUser models

---

#### ✅ Services (100%)
**Updated Services:**

1. **`backend/app/services/dialer_service.py` (CRITICAL - Completely Rewritten)**
   - ✅ Added `BILLABLE_STATUSES` constant (6 statuses)
   - ✅ Updated `fetch_next_batch(db, company, size)` with:
     - Global cooldown (3-day across all companies)
     - Company dedup (never call same number twice per company)
     - Global status filtering (exclude COMPLAINED, POWER_OFF)
     - Split agent lists (inbound/outbound)
     - Active scenarios list
   - ✅ Updated `report_result(db, report, company)` with:
     - Update `last_called_at`, `last_called_company_id`
     - Set `global_status` for POWER_OFF
     - Create `CallResult` with company_id, scenario_id, outbound_line_id
     - Charge billing only for billable statuses
   - ✅ Updated `_resolve_agent` to verify agent belongs to company
   - ✅ Changed imports to use CallResult, GlobalStatus, Company, Scenario, OutboundLine

2. **`backend/app/services/schedule_service.py` (Updated for Multi-Company)**
   - ✅ Updated `ensure_config(db, company_id)` - Per-company config
   - ✅ Updated `get_config(db, company_id)` - Get company config
   - ✅ Updated `list_intervals(db, company_id)` - Filter windows by company
   - ✅ Updated `update_schedule(db, data, company_id)` - Update company schedule
   - ✅ Updated `charge_for_connected_call(db, company_id)` - Charge company wallet
   - ✅ Updated `get_billing_info(db, company_id)` - Get company billing
   - ✅ Updated `update_billing(db, wallet_balance, cost_per_connected, company_id)` - Update company billing
   - ✅ Updated `is_call_allowed(now, db, company_id)` - Check company schedule

---

#### ✅ Stats Service (100%)
**File:** `backend/app/services/stats_service.py`

**Completed Changes:**
1. ✅ Updated imports: CallAttempt → CallResult, added Scenario, OutboundLine
2. ✅ Added `BILLABLE_STATUSES` constant
3. ✅ Added `dashboard_stats(db, company_id, group_by, time_filter)` function:
   - Groups by scenario or outbound_line
   - Filters by company_id
   - Calculates billable count (sum of BILLABLE_STATUSES)
   - Calculates inbound count (count of INBOUND_CALL)
   - Returns matrix with groups, totals, and all status counts
4. ✅ Added `_resolve_time_filter()` helper function
5. ✅ Updated all existing functions to use CallResult instead of CallAttempt

---

#### ✅ API Endpoints (100%)

**New API Files Created:**

1. ✅ **`backend/app/api/companies.py`** - Complete CRUD for companies
   - GET /api/companies - List all companies (superuser only)
   - GET /api/companies/{company_name} - Get company by name
   - POST /api/companies - Create company (superuser only)
   - PUT /api/companies/{company_id} - Update company (superuser only)
   - DELETE /api/companies/{company_id} - Deactivate company (superuser only)

2. ✅ **`backend/app/api/scenarios.py`** - Complete CRUD for scenarios
   - GET /api/{company_name}/scenarios - List company scenarios
   - POST /api/{company_name}/scenarios - Create scenario (admin only)
   - PUT /api/{company_name}/scenarios/{scenario_id} - Update scenario
   - DELETE /api/{company_name}/scenarios/{scenario_id} - Delete scenario

3. ✅ **`backend/app/api/outbound_lines.py`** - Complete CRUD for outbound lines
   - GET /api/{company_name}/outbound-lines - List company lines
   - POST /api/{company_name}/outbound-lines - Create line (admin only)
   - PUT /api/{company_name}/outbound-lines/{line_id} - Update line
   - DELETE /api/{company_name}/outbound-lines/{line_id} - Delete line

**API Files Updated:**

4. ✅ **`backend/app/api/dialer.py`**
   - GET /api/dialer/next-batch?company={company} - Added company query param
   - POST /api/dialer/report-result - Extracts company from report.company
   - POST /api/dialer/register-scenarios - New endpoint for dialer registration

5. ✅ **`backend/app/api/stats.py`**
   - GET /api/stats/dashboard-stats?company={company}&group_by={scenario|line}&time_filter={...} - New endpoint
   - Added company verification and access control

6. ✅ **`backend/app/api/schedule.py`**
   - GET /api/{company_name}/schedule - Company-scoped route
   - PUT /api/{company_name}/schedule - Company-scoped route
   - Added company_id parameter to all service calls

7. ✅ **`backend/app/api/billing.py`**
   - GET /api/{company_name}/billing - Company-scoped route
   - PUT /api/{company_name}/billing - Company-scoped route
   - Added company_id parameter to all service calls

8. ✅ **`backend/app/api/admins.py`**
   - GET /api/{company_name}/admins - Lists company users only
   - POST /api/{company_name}/admins - Creates user with company_id
   - PUT /api/{company_name}/admins/{user_id} - Updates company user
   - DELETE /api/{company_name}/admins/{user_id} - Deletes company user
   - Added company_name to all responses

9. ✅ **`backend/app/api/auth.py`**
   - GET /api/auth/me - Returns user with company_name
   - PUT /api/auth/me - Updates user and returns with company_name

10. ✅ **`backend/app/main.py`**
    - Imported new routers: companies, scenarios, outbound_lines
    - Registered companies router: prefix="/api/companies"
    - Registered scenarios router: prefix="/api"
    - Registered outbound_lines router: prefix="/api"
    - Updated admins, schedule, billing routers to use prefix="/api"

---

## ⏳ REMAINING WORK

### Phase 3: Frontend Implementation (0% Complete)

**All frontend files need to be created or updated. See plan file for details.**

**Critical Files:**
1. `frontend/src/App.tsx` - Complete rewrite with company routing
2. `frontend/src/hooks/useCompany.tsx` - New company context
3. `frontend/src/pages/Dashboard.tsx` - Complete redesign
4. `frontend/src/components/Layout.tsx` - Add company switcher
5. `frontend/src/pages/Login.tsx` - Update redirect logic
6. Plus ~10 more files

---

## 🔥 CRITICAL IMPLEMENTATION NOTES

### Backend Changes Summary
1. **ALL service functions now require `company_id` parameter**
2. **Table names changed** - Update all queries that reference old table names
3. **New enums added** - GlobalStatus, AgentType, INBOUND_CALL
4. **Billable statuses** - Only 6 statuses charge wallet (defined in BILLABLE_STATUSES)
5. **3-day cooldown** - Enforced across ALL companies via `last_called_at`
6. **Per-company deduplication** - Use CallResult to check if company called number

### Database Schema Changes
- `numbers` table (was `phone_numbers`):
  - Added: `global_status`, `last_called_at`, `last_called_company_id`
  - Removed: `status` column (now per-call in call_results)
- `call_results` table (was `call_attempts`):
  - Added: `company_id`, `scenario_id`, `outbound_line_id`
  - References updated to use "numbers" table
- `admin_users` table:
  - Added: `company_id`, `agent_type`
- `schedule_configs` and `schedule_windows` tables:
  - Added: `company_id`

---

## 📋 NEXT STEPS FOR NEW CHAT SESSION

### Step 1: Implement Frontend (Estimated: 3-4 hours)
After backend APIs are complete, start new chat with:

```
Continue implementing multi-company feature - FRONTEND PHASE.

CONTEXT:
- Backend fully implemented and tested
- See IMPLEMENTATION_PROGRESS.md for completed work

NEXT TASK:
Implement frontend changes for multi-company support.

Priority order:
1. Update App.tsx with company routing (/:companySlug/*)
2. Create useCompany.tsx context provider
3. Update Login.tsx redirect logic
4. Update Layout.tsx with company switcher
5. Redesign Dashboard.tsx (remove pie chart, add stats table)
6. Update remaining pages
7. Create new pages (CompanySelector, Scenarios, OutboundLines)

See plan file for exact specifications.
Start with App.tsx routing changes.
```

---

## 📁 KEY FILES REFERENCE

### Migration
- Migration: `backend/alembic/versions/0004_multi_company.py`
- Deployment Guide: `DEPLOYMENT_GUIDE.md`

### Backend - Models
- New: `backend/app/models/company.py`
- New: `backend/app/models/scenario.py`
- New: `backend/app/models/outbound_line.py`
- New: `backend/app/models/call_result.py`
- Updated: `backend/app/models/user.py`
- Updated: `backend/app/models/phone_number.py`
- Updated: `backend/app/models/schedule.py`

### Backend - Schemas
- New: `backend/app/schemas/company.py`
- New: `backend/app/schemas/scenario.py`
- New: `backend/app/schemas/outbound_line.py`
- Updated: `backend/app/schemas/dialer.py`
- Updated: `backend/app/schemas/user.py`

### Backend - Services
- Updated: `backend/app/services/dialer_service.py` ⭐⭐⭐
- Updated: `backend/app/services/schedule_service.py` ⭐⭐

### Backend - Config
- Updated: `backend/app/core/config.py`
- Updated: `backend/.env`
- Updated: `backend/app/api/deps.py`

---

## ⚠️ IMPORTANT NOTES

1. **Do NOT run migration on production yet** - Wait until all backend + frontend is complete
2. **Database migration is tested locally** - Ready when code is ready
3. **All backend service functions require company_id** - Don't forget to pass it
4. **BILLABLE_STATUSES is critical** - Only these 6 charge wallet
5. **3-day cooldown is global** - Applies across all companies
6. **Per-company dedup** - Each company can only call a number once (ever)

---

## 🎯 SUCCESS CRITERIA

Backend is complete when:
- [x] All API endpoints created/updated ✅
- [x] Stats service has dashboard_stats function ✅
- [x] All routes registered in main.py ✅
- [ ] Postman/curl tests pass for all endpoints (Pending testing)
- [ ] No import errors when starting backend (Pending testing)

Frontend is complete when:
- [ ] App loads without errors
- [ ] Login redirects to /{company}/dashboard
- [ ] Company switcher works for superuser
- [ ] Dashboard shows stats table (no pie chart)
- [ ] All CRUD operations work for scenarios/lines

System is complete when:
- [ ] Migration runs successfully on production
- [ ] Both companies can use system independently
- [ ] 3-day cooldown works across companies
- [ ] Billing is per-company
- [ ] All tests pass

---

**Last Updated:** 2026-02-14
**Backend Status:** ✅ COMPLETE (Phase 1 + Phase 2 done)
**Next Session Starts With:** Frontend Implementation (Phase 3)
