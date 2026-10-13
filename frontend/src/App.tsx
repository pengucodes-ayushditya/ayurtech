import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import {
  Leaf,
  LayoutDashboard,
  Users,
  Utensils,
  Activity,
  LogOut,
  Search,
  Plus,
  ArrowUpRight,
  ArrowLeft,
  Check,
  Clock,
  ChevronRight,
  Trash2,
  ClipboardList,
  ShieldCheck,
  Menu,
  X,
  BookOpen,
  Download,
} from 'lucide-react';
import { api, setCsrf } from './api';
import type { User, Patient, Food, Meal, Plan, Nutrition, Dashboard } from './types';
import { questions, doshas } from './questions';
import { previewNutrition } from './plan';
const meals = ['Breakfast', 'Mid-morning', 'Lunch', 'Evening snack', 'Dinner'];
const initials = (name: string) =>
  name
    .split(' ')
    .slice(0, 2)
    .map((n) => n[0])
    .join('');
const stamp = (value: string) =>
  new Date(value).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const message = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong');

function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const dialog = document.querySelector('.modal')!;
    const focusable = () =>
      Array.from(
        dialog.querySelectorAll<HTMLElement>(
          'button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href]',
        ),
      ).filter((e) => e.offsetParent !== null);
    focusable()[0]?.focus();
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'Tab') {
        const elements = focusable();
        const first = elements[0],
          last = elements[elements.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener('keydown', handler);
    return () => {
      document.removeEventListener('keydown', handler);
      previous?.focus();
    };
  }, []);
  return (
    <div className="overlay" onClick={onClose}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="section-head">
          <h2>{title}</h2>
          <button className="icon-btn" aria-label="Close dialog" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
function NutritionCards({ totals }: { totals: Nutrition }) {
  return (
    <div className="nutrition">
      {Object.entries(totals).map(([key, value]) => (
        <div key={key}>
          <small>{key}</small>
          <strong>
            {Math.round(value)}
            <span>{key === 'calories' ? ' kcal' : ' g'}</span>
          </strong>
        </div>
      ))}
    </div>
  );
}
function Auth({ onAuth }: { onAuth: (u: User) => void }) {
  const invite = new URLSearchParams(window.location.search).get('invite') || '';
  const [mode, setMode] = useState(invite ? 'claim' : 'login'),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    setBusy(true);
    const d = Object.fromEntries(new FormData(e.currentTarget));
    try {
      const result = await api<{ user: User; csrf: string }>(
        '/auth/' + mode,
        'POST',
        mode === 'claim' ? { ...d, token: invite } : d,
      );
      setCsrf(result.csrf);
      history.replaceState({}, '', location.pathname);
      onAuth(result.user);
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="auth">
      <div className="auth-story">
        <div className="brand">
          <Leaf />
          <span>
            ayurtech<span className="brand-dot">.</span>
          </span>
        </div>
        <div className="story-copy">
          <span className="eyebrow">CARE, WITH A CLEARER PICTURE</span>
          <h1>
            Traditional wisdom.
            <br />
            <em>Thoughtful practice.</em>
          </h1>
          <p>
            A connected workspace for personalized nutrition, patient progress, and a more
            intentional approach to care.
          </p>
          <div className="story-lines">
            <span>
              <ShieldCheck />
              Private patient records
            </span>
            <span>
              <Utensils />
              Personalized meal planning
            </span>
            <span>
              <Activity />A continuous care journey
            </span>
          </div>
        </div>
        <div className="story-footer">
          AYURVEDA × MODERN PRACTICE <span>01 / PRACTICE WORKSPACE</span>
        </div>
        <div className="circle circle-one" />
        <div className="circle circle-two" />
      </div>
      <section className="auth-form">
        <span className="eyebrow">YOUR PRACTICE, CONNECTED</span>
        <h2>
          {mode === 'register'
            ? 'Start your practice'
            : mode === 'claim'
              ? 'Activate your patient portal'
              : 'Welcome back'}
        </h2>
        <p>
          {mode === 'register'
            ? 'Create your own private dietitian workspace.'
            : mode === 'claim'
              ? 'Use the email your dietitian recorded for you.'
              : 'Sign in to your dietitian workspace or patient portal.'}
        </p>
        <form onSubmit={submit}>
          {mode === 'register' && (
            <>
              <label>
                Your name
                <input name="name" required minLength={2} maxLength={100} />
              </label>
              <label>
                Practice name
                <input name="clinic_name" required minLength={2} maxLength={100} />
              </label>
            </>
          )}
          <label>
            Email address
            <input
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              required
            />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              minLength={10}
              maxLength={128}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              placeholder="At least 10 characters"
              required
            />
          </label>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <button className="primary" disabled={busy}>
            {busy
              ? 'Please wait…'
              : mode === 'login'
                ? 'Sign in'
                : mode === 'claim'
                  ? 'Activate portal'
                  : 'Create workspace'}
            <ArrowUpRight size={17} />
          </button>
        </form>
        {!invite && (
          <p className="auth-toggle">
            {mode === 'login' ? 'New to AyurTech?' : 'Already have an account?'}{' '}
            <button
              onClick={() => {
                setMode(mode === 'login' ? 'register' : 'login');
                setError('');
              }}
            >
              {mode === 'login' ? 'Create a practice' : 'Sign in'}
            </button>
          </p>
        )}
        <div className="demo-note">
          <BookOpen size={18} />
          <div>
            <strong>Exploring the project?</strong>
            <p>
              Local seeded accounts: dietitian@ayurtech.demo or patient@ayurtech.demo
              <br />
              Password: AyurTechDemo!2026
            </p>
          </div>
        </div>
        <p className="footnote">Educational portfolio application. Use fictional patient data.</p>
      </section>
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null),
    [boot, setBoot] = useState(true),
    [view, setView] = useState('Overview'),
    [patients, setPatients] = useState<Patient[]>([]),
    [total, setTotal] = useState(0),
    [query, setQuery] = useState(''),
    [status, setStatus] = useState('active'),
    [offset, setOffset] = useState(0),
    [selected, setSelected] = useState<Patient | null>(null),
    [foods, setFoods] = useState<Food[]>([]),
    [dashboard, setDashboard] = useState<Dashboard | null>(null),
    [toast, setToast] = useState(''),
    [error, setError] = useState(''),
    [modal, setModal] = useState(''),
    [busy, setBusy] = useState(false),
    [mobile, setMobile] = useState(false),
    [inviteLink, setInviteLink] = useState('');
  const [planItems, setPlanItems] = useState<Meal[]>([]),
    [planTitle, setPlanTitle] = useState('Personalized daily plan'),
    [planNotes, setPlanNotes] = useState(''),
    [foodQuery, setFoodQuery] = useState(''),
    [assessmentKind, setAssessmentKind] = useState('prakriti');
  const requestVersion = useRef(0);
  const notify = (s: string) => {
    setToast(s);
    setTimeout(() => setToast(''), 4500);
  };
  const reload = useCallback(async () => {
    if (!user) return;
    const version = ++requestVersion.current;
    const [p, f, d] = await Promise.all([
      api<{ items: Patient[]; total: number }>(
        `/patients?q=${encodeURIComponent(query)}&status=${user.role === 'patient' ? 'all' : status}&offset=${offset}&limit=20`,
      ),
      api<{ items: Food[] }>('/foods'),
      user.role === 'dietitian' ? api<Dashboard>('/dashboard') : Promise.resolve(null),
    ]);
    if (version !== requestVersion.current) return;
    setPatients(p.items);
    setTotal(p.total);
    setFoods(f.items);
    setDashboard(d);
    if (user.role === 'patient' && p.items[0]) {
      const detail = await api<Patient>('/patients/' + p.items[0].id);
      if (version === requestVersion.current) setSelected(detail);
    }
  }, [user, query, status, offset]);
  useEffect(() => {
    api<{ user: User; csrf: string }>('/auth/me')
      .then((r) => {
        setCsrf(r.csrf);
        setUser(r.user);
      })
      .catch(() => {})
      .finally(() => setBoot(false));
  }, []);
  useEffect(() => {
    const timer = setTimeout(() => reload().catch((e) => setError(message(e))), 200);
    return () => clearTimeout(timer);
  }, [reload]);
  async function choose(p: Patient) {
    setError('');
    try {
      setSelected(await api<Patient>('/patients/' + p.id));
      setView('Patients');
    } catch (e) {
      setError(message(e));
    }
  }
  async function refreshPatient() {
    if (selected) setSelected(await api<Patient>('/patients/' + selected.id));
    await reload();
  }
  async function action(fn: () => Promise<void>) {
    setBusy(true);
    setError('');
    try {
      await fn();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    await action(async () => {
      await api('/auth/logout', 'POST');
      ++requestVersion.current;
      setPatients([]);
      setFoods([]);
      setDashboard(null);
      setTotal(0);
      setQuery('');
      setOffset(0);
      setStatus('active');
      setModal('');
      setInviteLink('');
      setPlanItems([]);
      setUser(null);
      setSelected(null);
      setView('Overview');
      setCsrf('');
    });
  }
  function startPlan() {
    const last = selected?.plans?.[0];
    setPlanItems(
      last?.items.map((i) => ({ meal: i.meal, food_id: i.food_id, grams: i.grams })) || [],
    );
    setPlanTitle(last?.title || 'Personalized daily plan');
    setPlanNotes(last?.notes || '');
    setModal('plan');
  }
  async function savePatient(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.currentTarget));
    await action(async () => {
      await api(
        '/patients' + (modal === 'edit' ? '/' + selected?.id : ''),
        modal === 'edit' ? 'PUT' : 'POST',
        {
          ...d,
          age: Number(d.age),
          allergies: String(d.allergies)
            .split(',')
            .map((a) => a.trim())
            .filter(Boolean),
        },
      );
      setModal('');
      await refreshPatient();
      notify(modal === 'edit' ? 'Patient updated' : 'Patient added to your practice');
    });
  }
  async function savePlan(e: FormEvent) {
    e.preventDefault();
    await action(async () => {
      await api('/patients/' + selected!.id + '/plans', 'POST', {
        title: planTitle,
        notes: planNotes,
        items: planItems,
        expected_version: selected!.plans?.[0]?.version || 0,
      });
      setModal('');
      await refreshPatient();
      notify('New plan version saved as draft');
    });
  }
  async function createInvite() {
    await action(async () => {
      const r = await api<{ token: string }>('/patients/' + selected!.id + '/invite', 'POST');
      setInviteLink(location.origin + '/?invite=' + encodeURIComponent(r.token));
      setModal('invite');
    });
  }
  function exportPlan(plan: Plan) {
    const data = {
      patient: selected?.name,
      plan,
      notice: 'Educational demo. Food values require professional verification.',
    };
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ayurtech-plan-v' + plan.version + '.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  if (boot)
    return (
      <div className="loading">
        <Leaf /> Opening your workspace…
      </div>
    );
  if (!user)
    return (
      <Auth
        onAuth={(u) => {
          setUser(u);
          setError('');
        }}
      />
    );
  const isDietitian = user.role === 'dietitian';
  const latest = selected?.plans?.find((p) => p.status === 'published');
  const assessment = selected?.assessments?.find((a) => a.kind === 'prakriti');
  const sections = isDietitian
    ? ([
        ['Overview', LayoutDashboard],
        ['Patients', Users],
        ['Food library', Utensils],
        ['About the project', BookOpen],
      ] as const)
    : ([
        ['My wellness', LayoutDashboard],
        ['Food library', Utensils],
        ['About the project', BookOpen],
      ] as const);
  const shownFoods = foods.filter((f) => f.name.toLowerCase().includes(foodQuery.toLowerCase()));
  return (
    <div className="workspace">
      <aside className={mobile ? 'sidebar open' : 'sidebar'}>
        <div className="brand">
          <Leaf />
          <span>
            ayurtech<span className="brand-dot">.</span>
          </span>
        </div>
        <div className="practice-tag">{isDietitian ? 'PRACTICE WORKSPACE' : 'PATIENT PORTAL'}</div>
        <nav>
          {sections.map(([label, Icon]) => (
            <button
              key={label}
              className={
                view === label || (label === 'My wellness' && view === 'Overview')
                  ? 'nav active'
                  : 'nav'
              }
              onClick={() => {
                setView(label);
                setError('');
                if (label === 'Patients') setSelected(null);
                setMobile(false);
              }}
            >
              <Icon size={19} />
              {label}
              {label === 'Patients' && <span>{dashboard?.active_patients || 0}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-tip">
          <div className="tip-icon">
            <Leaf size={20} />
          </div>
          <h4>Small steps. Lasting care.</h4>
          <p>Bring nutrition and patient progress into one thoughtful workflow.</p>
        </div>
        <div className="sidebar-user">
          <div className="avatar">{initials(user.name)}</div>
          <div>
            <strong>{user.name}</strong>
            <small>{isDietitian ? 'Dietitian' : 'Patient'}</small>
          </div>
          <button className="icon-btn" aria-label="Sign out" onClick={logout}>
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div>
            <button
              className="mobile-toggle icon-btn"
              aria-label="Toggle navigation"
              onClick={() => setMobile(!mobile)}
            >
              <Menu />
            </button>
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>
              {selected && isDietitian
                ? 'Patient profile'
                : view === 'Overview' && !isDietitian
                  ? 'My wellness'
                  : view}
            </strong>
          </div>
          <span className="top-date">
            <Clock size={14} />
            {new Date().toLocaleDateString(undefined, {
              weekday: 'short',
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </span>
        </header>
        <main className="content">
          {error && (
            <div className="error" role="alert">
              {error}
              <button onClick={() => setError('')} aria-label="Dismiss error">
                <X size={15} />
              </button>
            </div>
          )}
          {isDietitian && view === 'Overview' && (
            <>
              <div className="page-head">
                <div>
                  <span className="eyebrow">YOUR PRACTICE AT A GLANCE</span>
                  <h1>
                    A little clarity.
                    <br className="mobile-only" /> A lot of care.
                  </h1>
                  <p>
                    Welcome back, {user.name.replace(/^Dr\.\s*/, '').split(' ')[0]}. Here’s how your
                    practice is doing.
                  </p>
                </div>
                <button className="primary" onClick={() => setModal('add')}>
                  <Plus size={17} />
                  Add patient
                </button>
              </div>
              <section className="stats">
                {[
                  [
                    'Active patients',
                    dashboard?.active_patients || 0,
                    Users,
                    'Your current care community',
                  ],
                  [
                    'Published plans',
                    dashboard?.published_plans || 0,
                    Utensils,
                    'Personalized and ready to follow',
                  ],
                  [
                    'Assessments recorded',
                    dashboard?.assessed_patients || 0,
                    Activity,
                    'Understanding each constitution',
                  ],
                  [
                    'Awaiting a plan',
                    dashboard?.needs_plan || 0,
                    ClipboardList,
                    'Your next opportunities for care',
                  ],
                ].map(([label, value, Icon, subtitle]) => {
                  const I = Icon as typeof Users;
                  return (
                    <div className="stat" key={String(label)}>
                      <div>
                        <span>{String(label)}</span>
                        <I size={18} />
                      </div>
                      <strong>{String(value).padStart(2, '0')}</strong>
                      <small>{String(subtitle)}</small>
                    </div>
                  );
                })}
              </section>
              <div className="dashboard-grid">
                <section className="panel">
                  <div className="section-head">
                    <div>
                      <span className="eyebrow">PEOPLE, FIRST</span>
                      <h2>Your patients</h2>
                    </div>
                    <button
                      className="text-btn"
                      onClick={() => {
                        setView('Patients');
                        setSelected(null);
                      }}
                    >
                      View all
                      <ArrowUpRight size={16} />
                    </button>
                  </div>
                  <div className="patient-list">
                    {patients.slice(0, 5).map((p) => (
                      <button key={p.id} onClick={() => choose(p)}>
                        <div className="avatar pale">{initials(p.name)}</div>
                        <div>
                          <strong>{p.name}</strong>
                          <small>
                            {p.age} years · {p.gender}
                          </small>
                        </div>
                        <span className="badge">
                          {p.portal_active ? 'Portal active' : 'Invite pending'}
                        </span>
                        <ChevronRight size={16} />
                      </button>
                    ))}
                    {!patients.length && (
                      <Empty
                        label="Your care community starts here"
                        detail="Add your first patient to begin planning."
                      />
                    )}
                  </div>
                </section>
                <section className="care-card">
                  <span className="eyebrow">A MORE COMPLETE PICTURE</span>
                  <h2>
                    Every patient
                    <br />
                    has a story.
                  </h2>
                  <p>
                    Start with a profile. Understand their patterns. Build a plan that fits their
                    day.
                  </p>
                  <div className="care-illustration">
                    <div className="leaf-shape one" />
                    <div className="leaf-shape two" />
                    <div className="leaf-shape three" />
                    <div className="leaf-shape four" />
                    <div className="plant-stem" />
                  </div>
                  <button className="text-btn" onClick={() => setModal('add')}>
                    Begin a patient journey
                    <ArrowUpRight size={16} />
                  </button>
                </section>
              </div>
              <section className="panel activity-panel">
                <div className="section-head">
                  <h2>Practice activity</h2>
                  <span className="subtle">Latest updates</span>
                </div>
                {dashboard?.events.length ? (
                  dashboard.events.map((event) => (
                    <div className="activity-row" key={event.id}>
                      <span className="activity-dot" />
                      <span>{event.action.replaceAll('.', ' · ').replaceAll('_', ' ')}</span>
                      <time>{stamp(event.created_at)}</time>
                    </div>
                  ))
                ) : (
                  <p className="subtle">New activity will appear here as you care for patients.</p>
                )}
              </section>
            </>
          )}
          {isDietitian && view === 'Patients' && !selected && (
            <>
              <div className="page-head">
                <div>
                  <span className="eyebrow">YOUR CARE COMMUNITY</span>
                  <h1>Patients</h1>
                  <p>Profiles, progress, and personalized plans in one place.</p>
                </div>
                <button className="primary" onClick={() => setModal('add')}>
                  <Plus size={17} />
                  Add patient
                </button>
              </div>
              <div className="toolbar">
                <label className="search">
                  <Search size={18} />
                  <input
                    aria-label="Search patients"
                    placeholder="Search by patient name…"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setOffset(0);
                    }}
                  />
                </label>
                <select
                  aria-label="Patient status"
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="active">Active patients</option>
                  <option value="archived">Archived patients</option>
                  <option value="all">All patients</option>
                </select>
                <span className="subtle">{total} patients</span>
              </div>
              <section className="panel table-panel">
                <table>
                  <thead>
                    <tr>
                      <th>Patient</th>
                      <th>Age / gender</th>
                      <th>Allergies</th>
                      <th>Portal</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {patients.map((p) => (
                      <tr key={p.id}>
                        <td>
                          <button className="patient-name" onClick={() => choose(p)}>
                            <span className="avatar pale">{initials(p.name)}</span>
                            <span>
                              <strong>{p.name}</strong>
                              <small>{p.email}</small>
                            </span>
                          </button>
                        </td>
                        <td>
                          {p.age} · {p.gender}
                        </td>
                        <td>{p.allergies.join(', ') || 'None recorded'}</td>
                        <td>
                          <span className="badge">
                            {p.portal_active ? 'Active' : 'Not activated'}
                          </span>
                        </td>
                        <td>
                          <button
                            className="icon-btn"
                            aria-label={'Open ' + p.name}
                            onClick={() => choose(p)}
                          >
                            <ArrowUpRight size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!patients.length && (
                  <Empty
                    label="No patients found"
                    detail="Try a different search or add a patient."
                  />
                )}
                <div className="pagination">
                  <button
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - 20))}
                  >
                    Previous
                  </button>
                  <span>
                    {total ? offset + 1 : 0}–{Math.min(offset + 20, total)} of {total}
                  </span>
                  <button disabled={offset + 20 >= total} onClick={() => setOffset(offset + 20)}>
                    Next
                  </button>
                </div>
              </section>
            </>
          )}
          {((isDietitian && view === 'Patients' && selected) ||
            (!isDietitian && (view === 'Overview' || view === 'My wellness') && selected)) &&
            selected && (
              <>
                {isDietitian && (
                  <button className="text-btn back" onClick={() => setSelected(null)}>
                    <ArrowLeft size={16} />
                    All patients
                  </button>
                )}
                <div className="page-head">
                  <div>
                    <span className="eyebrow">
                      {isDietitian ? 'PATIENT JOURNEY' : 'YOUR CARE JOURNEY'}
                    </span>
                    <h1>{isDietitian ? selected.name : 'Your wellness, in focus.'}</h1>
                    <p>
                      {selected.age} years · {selected.gender} · {selected.email}
                    </p>
                  </div>
                  {isDietitian && (
                    <div className="button-row">
                      <button className="secondary" onClick={() => setModal('edit')}>
                        Edit profile
                      </button>
                      <button className="primary" onClick={startPlan}>
                        <Plus size={17} />
                        Build diet plan
                      </button>
                    </div>
                  )}
                </div>
                <div className="profile-grid">
                  <section className="panel">
                    <div className="section-head">
                      <h2>Ayurvedic profile</h2>
                      <Leaf size={18} />
                    </div>
                    <div className="dosha-display">
                      <small>Recorded constitution · Prakriti</small>
                      <h3>{assessment?.result || 'Not yet assessed'}</h3>
                      <p>
                        {selected.assessments?.find((a) => a.kind === 'vikriti')?.result
                          ? 'Current pattern: ' +
                            selected.assessments.find((a) => a.kind === 'vikriti')!.result
                          : 'Vikriti assessment not yet recorded'}
                      </p>
                    </div>
                    <div className="button-row">
                      <button
                        className="secondary"
                        onClick={() => {
                          setAssessmentKind('prakriti');
                          setModal('assessment');
                        }}
                      >
                        Prakriti assessment
                      </button>
                      <button
                        className="text-btn"
                        onClick={() => {
                          setAssessmentKind('vikriti');
                          setModal('assessment');
                        }}
                      >
                        Vikriti
                        <ArrowUpRight size={15} />
                      </button>
                    </div>
                    <p className="footnote">
                      Educational self-report questionnaire; not a diagnosis.
                    </p>
                  </section>
                  <section className="panel">
                    <div className="section-head">
                      <h2>Care notes</h2>
                      <ClipboardList size={18} />
                    </div>
                    <small className="eyebrow">RECORDED ALLERGIES</small>
                    <div className="allergies">
                      {selected.allergies.length ? (
                        selected.allergies.map((a) => (
                          <span key={a} className="badge amber">
                            {a}
                          </span>
                        ))
                      ) : (
                        <span className="subtle">None recorded</span>
                      )}
                    </div>
                    <p>{selected.notes || 'No additional notes recorded.'}</p>
                    {isDietitian && !selected.portal_active && (
                      <button className="text-btn" disabled={busy} onClick={createInvite}>
                        Create patient portal invitation
                        <ArrowUpRight size={16} />
                      </button>
                    )}
                    {selected.portal_active && (
                      <span className="subtle">
                        <Check size={14} /> Patient portal is connected
                      </span>
                    )}
                  </section>
                </div>
                <section className="panel">
                  <div className="section-head">
                    <div>
                      <span className="eyebrow">A PLAN FOR THE EVERYDAY</span>
                      <h2>{latest?.title || 'Daily diet plan'}</h2>
                    </div>
                    {latest && (
                      <div className="button-row">
                        <span className="badge">Published · v{latest.version}</span>
                        <button
                          className="icon-btn"
                          aria-label="Export plan JSON"
                          onClick={() => exportPlan(latest)}
                        >
                          <Download size={18} />
                        </button>
                      </div>
                    )}
                  </div>
                  {latest ? (
                    <>
                      <NutritionCards totals={latest.totals} />
                      <div className="meal-grid">
                        {meals.map((meal, i) => (
                          <div className="meal-card" key={meal}>
                            <span className="meal-number">0{i + 1}</span>
                            <h3>{meal}</h3>
                            {latest.items
                              .filter((item) => item.meal === meal)
                              .map((item, j) => (
                                <div className="meal-food" key={j}>
                                  <strong>{item.name}</strong>
                                  <small>
                                    {item.grams} g · {Math.round(item.nutrition?.calories || 0)}{' '}
                                    kcal
                                  </small>
                                </div>
                              ))}
                            {!latest.items.some((item) => item.meal === meal) && (
                              <p className="subtle">No items planned</p>
                            )}
                          </div>
                        ))}
                      </div>
                      {latest.notes && <p className="plan-notes">{latest.notes}</p>}
                    </>
                  ) : (
                    <Empty
                      label="A fresh start for a personalized plan"
                      detail={
                        isDietitian
                          ? 'Build a draft and publish it when ready.'
                          : 'Your dietitian will publish your plan here.'
                      }
                    />
                  )}
                </section>
                {isDietitian && (
                  <section className="panel">
                    <div className="section-head">
                      <h2>Plan versions</h2>
                      <span className="subtle">
                        Saved versions preserve food and nutrition snapshots
                      </span>
                    </div>
                    {selected.plans?.length ? (
                      selected.plans.map((p) => (
                        <div className="version-row" key={p.id}>
                          <div>
                            <strong>
                              v{p.version} · {p.title}
                            </strong>
                            <small>
                              {stamp(p.created_at)} · {Math.round(p.totals.calories)} kcal
                            </small>
                          </div>
                          <span className={'badge ' + (p.status === 'draft' ? 'amber' : '')}>
                            {p.status}
                          </span>
                          {p.status === 'draft' && p.version === selected.plans![0].version && (
                            <button
                              className="secondary"
                              disabled={busy}
                              onClick={() =>
                                action(async () => {
                                  await api(
                                    `/patients/${selected.id}/plans/${p.id}/publish`,
                                    'POST',
                                  );
                                  await refreshPatient();
                                  notify('Plan published to the patient portal');
                                })
                              }
                            >
                              Publish
                              <Check size={15} />
                            </button>
                          )}
                          <button
                            className="icon-btn"
                            aria-label={'Export version ' + p.version}
                            onClick={() => exportPlan(p)}
                          >
                            <Download size={16} />
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="subtle">No saved plans yet.</p>
                    )}
                  </section>
                )}
                <section className="panel">
                  <div className="section-head">
                    <div>
                      <span className="eyebrow">PROGRESS OVER PERFECTION</span>
                      <h2>Daily check-ins</h2>
                    </div>
                    <button className="secondary" onClick={() => setModal('checkin')}>
                      <Plus size={16} />
                      Record check-in
                    </button>
                  </div>
                  {selected.checkins?.length ? (
                    <div className="checkins">
                      {selected.checkins.map((c) => (
                        <div key={c.day}>
                          <strong>{c.day}</strong>
                          <span>
                            Plan adherence <b>{c.adherence}%</b>
                          </span>
                          <span>
                            Energy <b>{c.energy}/5</b>
                          </span>
                          <p>{c.note || 'No note added'}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="subtle">
                      Track adherence, energy, and a short reflection each day.
                    </p>
                  )}
                </section>
              </>
            )}
          {view === 'Food library' && (
            <>
              <div className="page-head">
                <div>
                  <span className="eyebrow">THE INGREDIENTS OF THOUGHTFUL CARE</span>
                  <h1>Food library</h1>
                  <p>
                    Explore nutrition alongside the Ayurvedic properties from your original demo.
                  </p>
                </div>
                <span className="badge">{foods.length} foods</span>
              </div>
              <div className="notice">
                <BookOpen size={18} />
                <span>
                  Illustrative hackathon data. Nutrient values, allergens, and Ayurvedic properties
                  require professional verification before clinical use.
                </span>
              </div>
              <label className="search food-search">
                <Search size={18} />
                <input
                  placeholder="Search foods…"
                  aria-label="Search food library"
                  value={foodQuery}
                  onChange={(e) => setFoodQuery(e.target.value)}
                />
              </label>
              <div className="food-grid">
                {shownFoods.map((f) => (
                  <article className="food-card" key={f.id}>
                    <div className="section-head">
                      <div className="food-icon">
                        <Utensils size={19} />
                      </div>
                      <span className={'badge ' + (f.properties.thermal === 'Hot' ? 'amber' : '')}>
                        {f.properties.thermal === 'Hot' ? 'Warming' : 'Cooling'}
                      </span>
                    </div>
                    <h3>{f.name}</h3>
                    <p className="subtle">
                      Per {f.unit} g · {f.properties.digestibility} digestion
                    </p>
                    <div className="food-macros">
                      <strong>
                        {f.nutrition.calories}
                        <small>kcal</small>
                      </strong>
                      <span>
                        {f.nutrition.protein} g<small>protein</small>
                      </span>
                      <span>
                        {f.nutrition.carbs} g<small>carbs</small>
                      </span>
                      <span>
                        {f.nutrition.fat} g<small>fat</small>
                      </span>
                    </div>
                    <div className="rasa">
                      {f.rasas.map((r) => (
                        <span key={r}>{r}</span>
                      ))}
                    </div>
                    {f.allergens.length > 0 && (
                      <small className="allergen-text">Contains: {f.allergens.join(', ')}</small>
                    )}
                  </article>
                ))}
              </div>
              {!shownFoods.length && (
                <Empty label="No matching foods" detail="Try another ingredient name." />
              )}
            </>
          )}
          {view === 'About the project' && (
            <>
              <div className="page-head">
                <div>
                  <span className="eyebrow">BUILT WITH INTENTION</span>
                  <h1>From prototype to platform.</h1>
                  <p>
                    A full-stack portfolio project built around Ayurvedic dietitian practice
                    management.
                  </p>
                </div>
              </div>
              <div className="profile-grid">
                <section className="panel">
                  <h2>The complete workflow</h2>
                  <ol className="about-list">
                    <li>Create a private dietitian practice.</li>
                    <li>Add a patient and record allergies.</li>
                    <li>Record educational constitution assessments.</li>
                    <li>Create a versioned diet plan with server-calculated nutrition.</li>
                    <li>Publish it and invite the patient to their portal.</li>
                    <li>Track daily adherence and energy.</li>
                  </ol>
                </section>
                <section className="panel">
                  <h2>Engineering behind the care</h2>
                  <p>React + TypeScript · FastAPI · SQLAlchemy · PostgreSQL / SQLite</p>
                  <p>
                    Clinic-scoped access, hashed session tokens, HttpOnly cookies, CSRF protection,
                    immutable plan versions, optimistic conflict detection, and structured audit
                    events.
                  </p>
                  <p>
                    Interactive API documentation is available at{' '}
                    <a href="/docs" target="_blank" rel="noreferrer">
                      /docs <ArrowUpRight size={13} />
                    </a>{' '}
                    when served from the backend.
                  </p>
                </section>
              </div>
              <div className="notice">
                <ShieldCheck size={20} />
                <span>
                  This release is a portfolio MVP with fictional data. Clinical validation, email
                  delivery, MFA, distributed rate limiting, encrypted backups, and production
                  monitoring remain deployment work.
                </span>
              </div>
            </>
          )}
          <footer className="workspace-footer">
            <span>
              <Leaf size={13} />
              AyurTech · Thoughtful care, connected.
            </span>
            <span>Educational portfolio project</span>
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Check size={18} />
          {toast}
        </div>
      )}
      {(modal === 'add' || modal === 'edit') && (
        <Modal
          title={modal === 'add' ? 'Add a patient' : 'Edit patient profile'}
          onClose={() => setModal('')}
        >
          <form onSubmit={savePatient}>
            <div className="form-grid">
              <label>
                Full name
                <input
                  name="name"
                  required
                  minLength={2}
                  maxLength={100}
                  defaultValue={modal === 'edit' ? selected?.name : ''}
                />
              </label>
              <label>
                Email address
                <input
                  name="email"
                  type="email"
                  required
                  defaultValue={modal === 'edit' ? selected?.email : ''}
                />
              </label>
              <label>
                Age (18+)
                <input
                  name="age"
                  type="number"
                  min={18}
                  max={120}
                  required
                  defaultValue={modal === 'edit' ? selected?.age : 30}
                />
              </label>
              <label>
                Gender
                <select
                  name="gender"
                  defaultValue={modal === 'edit' ? selected?.gender : 'Prefer not to say'}
                >
                  {['Female', 'Male', 'Other', 'Prefer not to say'].map((g) => (
                    <option key={g}>{g}</option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              Allergies (comma-separated)
              <input
                name="allergies"
                placeholder="e.g. milk, almonds, soy"
                defaultValue={modal === 'edit' ? selected?.allergies.join(', ') : ''}
              />
            </label>
            <label>
              Care notes
              <textarea
                name="notes"
                maxLength={2000}
                rows={3}
                defaultValue={modal === 'edit' ? selected?.notes : ''}
              />
            </label>
            {modal === 'edit' && (
              <label>
                Status
                <select name="status" defaultValue={selected?.status}>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </label>
            )}
            <p className="footnote">Record fictional data for this portfolio application.</p>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button className="primary" disabled={busy}>
              {busy ? 'Saving…' : 'Save patient'}
              <Check size={16} />
            </button>
          </form>
        </Modal>
      )}
      {modal === 'invite' && (
        <Modal title="Patient portal invitation" onClose={() => setModal('')}>
          <p>
            Share this private link with {selected?.name}. It expires in 48 hours. Creating a new
            invitation invalidates the previous one.
          </p>
          <label>
            Invitation link
            <input readOnly value={inviteLink} onFocus={(e) => e.currentTarget.select()} />
          </label>
          <button
            className="primary"
            onClick={() =>
              navigator.clipboard
                .writeText(inviteLink)
                .then(() => notify('Invitation copied'))
                .catch(() => setError('Select and copy the invitation link manually.'))
            }
          >
            Copy link
          </button>
          <p className="footnote">
            The patient must activate using {selected?.email} and choose a password.
          </p>
        </Modal>
      )}
      {modal === 'assessment' && (
        <Modal
          title={assessmentKind === 'prakriti' ? 'Prakriti assessment' : 'Vikriti assessment'}
          onClose={() => setModal('')}
        >
          <p>
            {assessmentKind === 'prakriti'
              ? 'Choose the patterns that best describe long-term tendencies.'
              : 'Choose the patterns that best describe the current experience.'}{' '}
            This questionnaire is educational and is not clinically validated.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const d = new FormData(e.currentTarget);
              action(async () => {
                await api(`/patients/${selected!.id}/assessments`, 'POST', {
                  kind: assessmentKind,
                  answers: questions.map((_, i) => d.get('q' + i)),
                });
                setModal('');
                await refreshPatient();
                notify('Assessment recorded');
              });
            }}
          >
            {questions.map((q, i) => (
              <fieldset key={q.label}>
                <legend>
                  {i + 1}. {q.label}
                </legend>
                {q.options.map((o, j) => (
                  <label className="radio-option" key={o}>
                    <input type="radio" name={'q' + i} value={doshas[j]} required />
                    {o}
                  </label>
                ))}
              </fieldset>
            ))}
            {error && <p className="error">{error}</p>}
            <button className="primary" disabled={busy}>
              {busy ? 'Saving…' : 'Record assessment'}
              <Check size={16} />
            </button>
          </form>
        </Modal>
      )}
      {modal === 'plan' && (
        <Modal title="Build a daily diet plan" onClose={() => setModal('')}>
          <form onSubmit={savePlan}>
            <label>
              Plan title
              <input
                value={planTitle}
                onChange={(e) => setPlanTitle(e.target.value)}
                minLength={2}
                maxLength={120}
                required
              />
            </label>
            <NutritionCards totals={previewNutrition(planItems, foods)} />
            <p className="footnote">
              Preview totals. The server calculates and saves authoritative nutrition values.
            </p>
            <div className="plan-editor">
              {planItems.map((item, i) => (
                <div className="plan-item" key={i}>
                  <select
                    aria-label={'Meal ' + (i + 1)}
                    value={item.meal}
                    onChange={(e) =>
                      setPlanItems(
                        planItems.map((x, j) => (j === i ? { ...x, meal: e.target.value } : x)),
                      )
                    }
                  >
                    {meals.map((m) => (
                      <option key={m}>{m}</option>
                    ))}
                  </select>
                  <select
                    aria-label={'Food ' + (i + 1)}
                    value={item.food_id}
                    onChange={(e) =>
                      setPlanItems(
                        planItems.map((x, j) => (j === i ? { ...x, food_id: e.target.value } : x)),
                      )
                    }
                  >
                    {foods.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name}
                      </option>
                    ))}
                  </select>
                  <label className="grams">
                    <input
                      aria-label={'Grams ' + (i + 1)}
                      type="number"
                      min={1}
                      max={2000}
                      required
                      value={item.grams}
                      onChange={(e) =>
                        setPlanItems(
                          planItems.map((x, j) =>
                            j === i ? { ...x, grams: Number(e.target.value) } : x,
                          ),
                        )
                      }
                    />
                    g
                  </label>
                  <button
                    type="button"
                    className="icon-btn"
                    aria-label={'Remove food ' + (i + 1)}
                    onClick={() => setPlanItems(planItems.filter((_, j) => j !== i))}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
            <button
              type="button"
              className="secondary"
              disabled={!foods.length || planItems.length >= 60}
              onClick={() =>
                setPlanItems([
                  ...planItems,
                  { meal: 'Breakfast', food_id: foods[0].id, grams: 100 },
                ])
              }
            >
              <Plus size={16} />
              Add food
            </button>
            <label>
              Plan notes
              <textarea
                maxLength={2000}
                rows={3}
                value={planNotes}
                onChange={(e) => setPlanNotes(e.target.value)}
                placeholder="Meal timing, preferences, or follow-up notes…"
              />
            </label>
            <div className="notice compact">
              Recorded allergies: {selected?.allergies.join(', ') || 'none'}. Conflicting foods are
              rejected on save and publication.
            </div>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button className="primary" disabled={busy || !planItems.length}>
              {busy ? 'Saving…' : 'Save new draft version'}
              <Check size={16} />
            </button>
          </form>
        </Modal>
      )}
      {modal === 'checkin' && (
        <Modal title="Record a daily check-in" onClose={() => setModal('')}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const d = Object.fromEntries(new FormData(e.currentTarget));
              action(async () => {
                await api(`/patients/${selected!.id}/checkins`, 'POST', {
                  ...d,
                  adherence: Number(d.adherence),
                  energy: Number(d.energy),
                });
                setModal('');
                await refreshPatient();
                notify('Daily check-in recorded');
              });
            }}
          >
            <label>
              Date
              <input name="day" type="date" required max={today()} defaultValue={today()} />
            </label>
            <label>
              Plan adherence (%)
              <input name="adherence" type="number" min={0} max={100} required defaultValue={80} />
            </label>
            <label>
              Energy (1 = low, 5 = high)
              <select name="energy" defaultValue="3">
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
            <label>
              Reflection
              <textarea name="note" maxLength={1000} rows={3} />
            </label>
            <p className="footnote">Saving on the same date updates the previous check-in.</p>
            {error && <p className="error">{error}</p>}
            <button className="primary" disabled={busy}>
              Save check-in
              <Check size={16} />
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
function Empty({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="empty">
      <Leaf size={25} />
      <h3>{label}</h3>
      <p>{detail}</p>
    </div>
  );
}
