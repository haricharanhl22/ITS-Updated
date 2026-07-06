-- =============================================================================
-- Migration: 005_add_student_fk_constraints.sql
--
-- Problem: student_mastery, learning_events, generated_assessments, and
-- messages all store a student_id with NO foreign key back to users(id).
-- Without that constraint, deleting or resetting a user never cleans up their
-- rows in those tables. If the users.id identity sequence is ever restarted
-- (e.g. TRUNCATE users RESTART IDENTITY, or manually clearing test accounts),
-- a brand-new registration can be handed an id that still has old
-- student_mastery/learning_events rows attached to it — making a fresh
-- account appear to already have progress (this is what caused new users to
-- show non-zero mastery immediately after registering).
--
-- Fix: add `references users(id) on delete cascade` to every student_id
-- column. This also means Postgres will now refuse a bare `TRUNCATE users`
-- (it requires `TRUNCATE users CASCADE` or deleting dependents first), which
-- is a deliberate safety net against silently orphaning rows again.
--
-- Run in Supabase SQL Editor (Dashboard -> SQL Editor -> New Query).
--
-- IMPORTANT: if any ALTER below fails with a type-mismatch error (e.g.
-- "foreign key constraint ... cannot be implemented" / operator does not
-- exist uuid = bigint), it means that table's student_id column is not
-- actually the same type as users.id in your database yet. Stop and fix the
-- column type first — do not blindly retry or skip the failing block.
-- =============================================================================

do $$
begin
    if not exists (
        select 1 from information_schema.table_constraints
        where constraint_name = 'student_mastery_student_id_fkey'
    ) then
        alter table student_mastery
            add constraint student_mastery_student_id_fkey
            foreign key (student_id) references users(id) on delete cascade;
    end if;
end $$;

do $$
begin
    if not exists (
        select 1 from information_schema.table_constraints
        where constraint_name = 'learning_events_student_id_fkey'
    ) then
        alter table learning_events
            add constraint learning_events_student_id_fkey
            foreign key (student_id) references users(id) on delete cascade;
    end if;
end $$;

do $$
begin
    if not exists (
        select 1 from information_schema.table_constraints
        where constraint_name = 'generated_assessments_student_id_fkey'
    ) then
        alter table generated_assessments
            add constraint generated_assessments_student_id_fkey
            foreign key (student_id) references users(id) on delete cascade;
    end if;
end $$;

do $$
begin
    if not exists (
        select 1 from information_schema.table_constraints
        where constraint_name = 'messages_student_id_fkey'
    ) then
        alter table messages
            add constraint messages_student_id_fkey
            foreign key (student_id) references users(id) on delete cascade;
    end if;
end $$;
