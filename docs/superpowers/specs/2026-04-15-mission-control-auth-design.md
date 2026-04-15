# Mission Control Auth Gate — Design Spec

**Date:** 2026-04-15  
**Status:** Approved  
**Scope:** Add a Supabase-authenticated `/mission-control` page to the METSAnauts Next.js website that embeds the Flask mission control UI in an iframe, accessible only to allowlisted team members.

---

## Problem

The Flask mission control app (map, commands, AI assistant) needs to be accessible to the team for remote testing, but should not be publicly visible. The website already exists as Next.js at metsanauts-website/. The solution is temporary — just for testing — so embedding via iframe is preferred over porting.

---

## Architecture

```
Browser
  └── Next.js (metsanauts-website)
        ├── /mission-control/login   — Supabase email/password login
        ├── /mission-control         — Protected page (iframe → Flask)
        └── middleware.ts            — Checks Supabase session + allowlist

Supabase
  ├── Auth — email/password
  └── Table: allowed_users (id uuid, email text)

Flask app (running separately on local network)
  └── Embedded via iframe at NEXT_PUBLIC_MISSION_CONTROL_URL
```

---

## Pages

### `/mission-control/login`
- Email + password form
- Uses `@supabase/ssr` to sign in
- On success → redirect to `/mission-control`
- On failure → show error message
- No sign-up — accounts are created manually by the team lead

### `/mission-control`
- Server component checks Supabase session
- Queries `allowed_users` table for the logged-in user's UUID
- If not found → redirect to `/mission-control/login`
- If found → render full-screen `<iframe>` pointing at Flask URL
- Logout button in top-right corner

---

## Supabase Schema

```sql
create table allowed_users (
  id uuid primary key references auth.users(id),
  email text not null
);
```

Rows are added manually by the team lead via Supabase dashboard. To grant access: create a user in Supabase Auth, then insert their UUID into `allowed_users`.

---

## Environment Variables

```env
NEXT_PUBLIC_SUPABASE_URL=<your supabase project url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your supabase anon key>
NEXT_PUBLIC_MISSION_CONTROL_URL=http://192.168.55.1:5000
```

---

## Auth Middleware

`middleware.ts` at the Next.js root:
- Intercepts all requests to `/mission-control/*`
- Refreshes the Supabase session cookie
- If no session → redirect to `/mission-control/login`
- Allowlist check happens in the server component (not middleware) to keep middleware fast

---

## Packages Required

- `@supabase/supabase-js`
- `@supabase/ssr`

---

## Out of Scope

- Sign-up flow (accounts created manually)
- Role-based permissions beyond the allowlist
- Porting Flask UI into Next.js
- Any changes to the Flask app itself
