# Techno Terminal — Requirements Analysis

## 1. Company Overview

**Techno Terminal / Techno Future KFS** is a tech and robotics education center for children and teens. It offers courses in software (HTML, CSS, JS, Scratch, Database), hardware/robotics (EV3, WEDO, Spike, Arduino), and STEAM fields. The center also participates in international competitions (FLL, Robofest, Afro-Asian Forum, etc.).

---

## 2. Core Concepts

### 2.1 Students

- A student is a child/teen registered by their parent/guardian.
- A student has: name, date of birth, gender, and enrollment history.
- **Contact info** (phone, whatsapp) belongs to the **guardian**, not the student.
- A student can be in **multiple groups** simultaneously (different courses).
- A student can **move freely** between groups (any course, any level).
- The system must track a student's **full history**: every group, every session attended, every payment, every competition.
- **Siblings**: Detected via `guardian_id`. Students sharing the same guardian are siblings. The system **auto-detects and flags** siblings. The admin decides whether to apply a discount (50 EGP off per level for both).

### 2.2 Groups

- A group is the core operational unit — a recurring class.
- A group is defined by: **course, day, time, instructor, and student roster**.
- A group is **long-lived**. It doesn't end after 5 sessions. It keeps going.
- Every **5 sessions = 1 level**. The level counter ticks up automatically. After session 10, the group is on Level 3.
- The group **name is auto-generated** from: day + time + course name + competition tag (if applicable).
- Students usually join at the **start of a new level**, but the admin makes the final call based on: age compatibility, prior course history, and skill level.
- A group's schedule (day/time) **can change** at any time.
- A group has a **max capacity** (soft limit, admin override allowed).

### 2.3 Courses & Pricing

- **Software courses**: 650 EGP per level (5 sessions).
- **Hardware/Robotics courses**: 550 EGP per level (5 sessions).
- Prices are **flexible** and may change. The system should allow editing prices.
- Each student in a group may pay a **custom amount** (set at enrollment).

### 2.4 Sessions & Attendance

- A session is one class meeting on a specific date.
- Usually **1 session per week**, but extra sessions can occur mid-week.
- Attendance is marked **before** the session starts by the system admin.
- Status options: present / absent.
- If the regular instructor is absent, a **substitute** covers the session. This session must be **flagged**.

### 2.5 Payments

- Parents pay the **full level amount at once** (not per session).
- Payment can happen at the start of the level or during it.
- When a student **transfers** groups, their payment follows them — sessions already attended are accounted for.
- The system should track: amount, date, method (cash/card/transfer), who received it.
- **Sibling discount**: System detects siblings automatically. Admin chooses whether to apply the 50 EGP discount.

---

## 3. Competitions

- The center participates in competitions: FLL, Robofest, Afro-Asian Forum, WRO, and others.
- Competitions are **annual** events (FLL 2023, FLL 2024, Afro-Asian 2025, etc.).
- Each competition has **categories**:
  - FLL: Explore, Challenge, Discover
  - Afro-Asian: Software Leaders, Game to Gain, Marketing, Inventor, etc.
- **Teams** are formed ~5 months before competition day.
- A team is typically a subset of students from the **same group and level**.
- Each student enrolling in a competition pays an **enrollment fee** (per student, not per team).
- Teams have: name, coach (instructor), and a list of student members.
- Competition enrollment fees must be tracked separately from course payments.

---

## 4. Employees

### 4.1 Part-Time

- Works 3 days/week, 8 hours/day.
- Paid a **fixed monthly salary**.
- Payroll calculated at end of month based on attendance.

### 4.2 Contract

- Gets paid **per level completed** in each of their groups.
- Formula: `(number_of_students × price_per_level) × 25%`
- Example: 5 students × 550 = 2,750 → instructor gets 687.50 EGP.
- No mandatory office hours — just attend their group sessions.
- Payroll is **not monthly**. It's triggered when levels end, which varies by group.
- The system should **notify the admin** when a level completes and show: instructor name, group, student count, and calculated amount.

### 4.3 Payroll (Deferred to V2)

- Payroll features are **not required for the first version**.
- V1 should only track employee info and attendance.
- V2 will add auto-calculation and payment records.

---

## 5. User Roles

| Role | Access |
|---|---|
| **Admin** | Full access to everything. Can manage users, courses, financial data. |
| **System Admin** | Day-to-day operations: register students, mark attendance, collect payments, manage groups. |
| Student/Parent portal | **Deferred** to future versions. |

---

## 6. Daily Workflow

### Registering a New Student

1. Parent calls or visits.
2. System admin creates or finds the **guardian** record (name, phone, whatsapp).
3. System admin creates the **student** record linked to the guardian.
4. System checks for **siblings** (other students with the same guardian) and flags if found.
5. System admin finds a suitable group based on: course interest, age, skill level, schedule.
6. Student is enrolled in the group. Payment amount is set.

### Running a Session

1. Before the session, the system admin opens the group's attendance sheet.
2. Marks each student as present or absent.
3. If the instructor is absent, a substitute is assigned and the session is flagged.
4. The system auto-tracks session count toward the current level.

### Payments

1. Parent comes in to pay for a level.
2. System admin checks if the student has a sibling → system flags it.
3. Admin decides whether to apply discount.
4. Admin records the payment: amount, method, date.

### End of Level

1. After 5 sessions in a group, the level auto-increments.
2. If the instructor is contract-type, the system notifies the admin of the payroll due.
3. New payment cycle begins for the next level.

---

## 7. Key Design Principles

> [!IMPORTANT]
> These business rules are **flexible guidelines**, not rigid database constraints.
> The application should **assist and suggest**, not block the admin from making decisions.

1. **The admin is always right.** The system suggests (e.g., "this student has a sibling"), but the admin decides (e.g., whether to apply the discount).
2. **Rules can change.** Session counts, pricing, discount amounts — all should be editable, not hardcoded.
3. **Keep it simple.** The system should feel like a smart spreadsheet replacement, not an enterprise ERP.
4. **Full audit trail.** Every action (enrollment, payment, transfer, attendance) should be timestamped and traceable.
