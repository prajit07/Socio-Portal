const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

// Find Edge or Chrome executable path
function getBrowserPath() {
  const paths = [
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  ];
  for (const p of paths) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error("No Chrome or Edge executable found!");
}

const TOKENS_PATH = path.join(__dirname, 'demo_tokens.json');
const OUT_DIR = path.join(__dirname);

if (!fs.existsSync(TOKENS_PATH)) {
  console.error("demo_tokens.json not found!");
  process.exit(1);
}

const tokensData = JSON.parse(fs.readFileSync(TOKENS_PATH, 'utf-8'));
const { tokens, profiles, problem_ids } = tokensData;
const sampleProblemId = (problem_ids && problem_ids.length > 0) ? problem_ids[0] : 'prob_4ykcy1266x';

// List of all 50 screenshots with their specifications
const SCREENSHOT_SPECS = [
  // Public & Unauth Pages
  { id: "01-landing", url: "http://localhost:5173/", role: null, mobile: false },
  { id: "02-login", url: "http://localhost:5173/login", role: null, mobile: false },
  { id: "03-register", url: "http://localhost:5173/register", role: null, mobile: false },
  { id: "04-not-found", url: "http://localhost:5173/404-not-found-page", role: null, mobile: false },
  { id: "05-public-map", url: "http://localhost:5173/map", role: null, mobile: false },
  
  // OTP steps (interactive UI actions)
  { id: "06-login-otp-step", url: "http://localhost:5173/login", role: null, mobile: false, action: "login_otp" },
  { id: "07-register-otp-step", url: "http://localhost:5173/register", role: null, mobile: false, action: "register_otp" },
  
  // Citizen Pages
  { id: "08-citizen-dashboard", url: "http://localhost:5173/dashboard", role: "citizen", mobile: false },
  { id: "09-submit-problem", url: "http://localhost:5173/problems/new", role: "citizen", mobile: false },
  { id: "10-problems-list", url: "http://localhost:5173/problems", role: "citizen", mobile: false },
  { id: "11-problems-search", url: "http://localhost:5173/problems?search=water", role: "citizen", mobile: false },
  { id: "12-problem-detail-open", url: `http://localhost:5173/problems/${sampleProblemId}`, role: "citizen", mobile: false },
  { id: "13-problem-detail-pending", url: `http://localhost:5173/problems/${sampleProblemId}`, role: "citizen", mobile: false },
  { id: "14-problem-detail-implemented", url: `http://localhost:5173/problems/${sampleProblemId}`, role: "citizen", mobile: false },
  { id: "15-solution-detail", url: "http://localhost:5173/solutions/1", role: "citizen", mobile: false },
  { id: "16-map-view", url: "http://localhost:5173/map", role: "citizen", mobile: false },
  { id: "17-notifications", url: "http://localhost:5173/notifications", role: "citizen", mobile: false },
  { id: "18-settings", url: "http://localhost:5173/settings", role: "citizen", mobile: false },
  { id: "50-landing-auth-citizen", url: "http://localhost:5173/", role: "citizen", mobile: false },

  // University Admin Pages
  { id: "19-uni-dashboard", url: "http://localhost:5173/dashboard", role: "university_admin", mobile: false },
  { id: "20-uni-teams", url: "http://localhost:5173/university/teams", role: "university_admin", mobile: false },
  { id: "21-uni-proposals", url: "http://localhost:5173/university/proposals", role: "university_admin", mobile: false },
  { id: "22-uni-students", url: "http://localhost:5173/university/students", role: "university_admin", mobile: false },
  { id: "23-team-create", url: "http://localhost:5173/teams/new", role: "university_admin", mobile: false },
  { id: "24-team-workspace", url: "http://localhost:5173/teams/1", role: "university_admin", mobile: false },
  { id: "25-proposal-editor-new", url: "http://localhost:5173/proposals/new", role: "university_admin", mobile: false },
  { id: "26-proposal-editor-edit", url: "http://localhost:5173/proposals/1/edit", role: "university_admin", mobile: false },

  // Student Pages
  { id: "27-uni-dashboard-student", url: "http://localhost:5173/dashboard", role: "student", mobile: false },
  { id: "28-team-workspace-student", url: "http://localhost:5173/teams/1", role: "student", mobile: false },

  // Faculty Pages
  { id: "29-uni-dashboard-faculty", url: "http://localhost:5173/dashboard", role: "faculty", mobile: false },

  // Industry Pages
  { id: "30-industry-proposals", url: "http://localhost:5173/industry/proposals", role: "industry", mobile: false },
  { id: "31-industry-collab", url: "http://localhost:5173/industry/collaborations", role: "industry", mobile: false },
  { id: "32-industry-feed", url: "http://localhost:5173/industry/feed", role: "industry", mobile: false },
  { id: "33-industry-profile", url: "http://localhost:5173/industry/profile", role: "industry", mobile: false },
  { id: "34-collab-workspace", url: "http://localhost:5173/collaborations/1", role: "industry", mobile: false },
  { id: "35-collab-workspace-new", url: "http://localhost:5173/collaborations/new", role: "industry", mobile: false },
  { id: "49-notifications-industry", url: "http://localhost:5173/notifications", role: "industry", mobile: false },

  // Government Pages
  { id: "36-gov-dashboard", url: "http://localhost:5173/dashboard", role: "government", mobile: false },
  { id: "37-gov-analytics", url: "http://localhost:5173/government/analytics", role: "government", mobile: false },
  { id: "38-gov-impact-reports", url: "http://localhost:5173/government/reports", role: "government", mobile: false },

  // Admin Pages
  { id: "39-admin-users", url: "http://localhost:5173/admin/users", role: "admin", mobile: false },
  { id: "40-admin-moderation", url: "http://localhost:5173/admin/moderation", role: "admin", mobile: false },
  { id: "41-admin-ai", url: "http://localhost:5173/admin/ai-insights", role: "admin", mobile: false },
  { id: "42-admin-broadcast", url: "http://localhost:5173/admin/broadcast", role: "admin", mobile: false },

  // Mobile Viewport Pages
  { id: "43-landing-mobile", url: "http://localhost:5173/", role: null, mobile: true },
  { id: "44-login-mobile", url: "http://localhost:5173/login", role: null, mobile: true },
  { id: "45-register-mobile", url: "http://localhost:5173/register", role: null, mobile: true },
  { id: "46-problems-mobile", url: "http://localhost:5173/problems", role: "citizen", mobile: true },
  { id: "47-citizen-dashboard-mobile", url: "http://localhost:5173/dashboard", role: "citizen", mobile: true },
  { id: "48-submit-problem-mobile", url: "http://localhost:5173/problems/new", role: "citizen", mobile: true },
];

async function run() {
  const executablePath = getBrowserPath();
  console.log("Using browser:", executablePath);

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  for (let i = 0; i < SCREENSHOT_SPECS.length; i++) {
    const spec = SCREENSHOT_SPECS[i];
    console.log(`[${i + 1}/50] Capturing ${spec.id}...`);

    // Set Viewport
    if (spec.mobile) {
      await page.setViewport({ width: 390, height: 844, isMobile: true });
    } else {
      await page.setViewport({ width: 1920, height: 1080 });
    }

    // Auth injection
    if (spec.role) {
      const token = tokens[spec.role];
      const profile = profiles[spec.role];
      await page.goto("http://localhost:5173/login", { waitUntil: 'networkidle0' });
      await page.evaluate((t, p) => {
        localStorage.setItem('token', t);
        localStorage.setItem('user', JSON.stringify(p));
      }, token, profile);
    } else {
      await page.goto("http://localhost:5173/login", { waitUntil: 'networkidle0' });
      await page.evaluate(() => {
        localStorage.clear();
      });
    }

    // Navigate to target URL
    await page.goto(spec.url, { waitUntil: 'networkidle0' }).catch(() => {});
    await new Promise(r => setTimeout(r, 1200)); // allow components to settle

    // Special actions if needed
    if (spec.action === "login_otp") {
      try {
        const input = await page.$('input[type="email"]');
        if (input) {
          await input.type('demo_citizen@test.com');
          const btn = await page.$('button[type="submit"]');
          if (btn) await btn.click();
          await new Promise(r => setTimeout(r, 800));
        }
      } catch (e) {}
    } else if (spec.action === "register_otp") {
      try {
        const nameInput = await page.$('input[name="name"]');
        if (nameInput) await nameInput.type('New Citizen');
        const emailInput = await page.$('input[type="email"]');
        if (emailInput) await emailInput.type('new_citizen@test.com');
        const passInput = await page.$('input[type="password"]');
        if (passInput) await passInput.type('Demo1234!');
        const btn = await page.$('button[type="submit"]');
        if (btn) await btn.click();
        await new Promise(r => setTimeout(r, 800));
      } catch (e) {}
    }

    // Save screenshot
    const outPath = path.join(OUT_DIR, `${spec.id}.png`);
    await page.screenshot({ path: outPath, fullPage: false });
    console.log(`  Saved: ${outPath}`);
  }

  await browser.close();
  console.log("\n=== ALL 50 SCREENSHOTS CAPTURED SUCCESSFULLY ===");
}

run().catch(err => {
  console.error("Fatal Error:", err);
  process.exit(1);
});
