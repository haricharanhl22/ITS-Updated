-- =============================================================================
-- Maintenance script: cleanup_orphaned_student_rows.sql
-- NOT an automatic migration — review the SELECT output before running any
-- DELETE below. Run this AFTER applying
-- supabase/migrations/005_add_student_fk_constraints.sql.
--
-- Purpose: find and remove student_mastery / learning_events /
-- generated_assessments / messages rows whose student_id no longer matches
-- any row in users — these are true orphans (e.g. left over from a deleted
-- test account whose id was later reused, or a manually truncated users
-- table). They are safe to delete because no current user owns them.
--
-- This does NOT fix the specific case where an existing, currently-real user
-- was handed a recycled id that still has another (also currently-real)
-- user's old data attached — that can only happen once, going forward
-- migration 005's FK constraints prevent it from recurring. If you suspect
-- that already happened to a specific account, inspect that student_id's
-- rows manually (created_at timestamps vs. the user's actual registration
-- date) rather than relying on this script.
-- =============================================================================

-- ── 1. Preview — run these first and read the output ────────────────────────
select 'student_mastery' as table_name, student_id, concept_name, mastery_score, last_updated
from student_mastery
where student_id not in (select id from users);

select 'learning_events' as table_name, student_id, concept_name, score, created_at
from learning_events
where student_id not in (select id from users);

select 'generated_assessments' as table_name, student_id, concept_name, difficulty, created_at
from generated_assessments
where student_id not in (select id from users);

select 'messages' as table_name, student_id, role, created_at
from messages
where student_id not in (select id from users);

-- ── 2. Delete — only after confirming the preview rows are truly orphaned ──
-- Uncomment and run these once you're satisfied:

-- delete from student_mastery where student_id not in (select id from users);
-- delete from learning_events where student_id not in (select id from users);
-- delete from generated_assessments where student_id not in (select id from users);
-- delete from messages where student_id not in (select id from users);
