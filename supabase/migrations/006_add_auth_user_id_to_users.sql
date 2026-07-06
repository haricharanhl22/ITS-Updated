-- =============================================================================
-- Migration: 006_add_auth_user_id_to_users.sql
--
-- Problem: get_current_student() (backend/app/auth/auth_service.py) links a
-- Supabase Auth session to a row in the custom `users` table by EMAIL. Email
-- is not a stable identity: if someone deletes their Supabase Auth account
-- (e.g. via the Supabase dashboard, or during testing) and registers again
-- with the SAME email, Supabase issues a brand-new auth user id, but our
-- lookup-by-email still finds the OLD `users` row and hands back its
-- existing student_id — silently resurrecting all of that row's old
-- mastery/XP/history onto what the person believes is a fresh account.
--
-- Fix: give `users` a stable link to the actual Supabase Auth user id
-- (`auth_user_id`), so lookups can key off that immutable identifier instead
-- of the reusable email address. See auth_service.py for the updated lookup
-- logic that uses this column.
--
-- Run in Supabase SQL Editor (Dashboard -> SQL Editor -> New Query).
-- =============================================================================

alter table users
    add column if not exists auth_user_id uuid;

create unique index if not exists users_auth_user_id_key
    on users (auth_user_id)
    where auth_user_id is not null;
