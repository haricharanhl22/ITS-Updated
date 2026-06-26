-- Enable RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;

-- Create policies for messages
CREATE POLICY "Users can insert their own messages" ON messages
    FOR INSERT WITH CHECK (student_id::uuid = auth.uid());

CREATE POLICY "Users can select their own messages" ON messages
    FOR SELECT USING (student_id::uuid = auth.uid());

-- Create policies for learning_events
CREATE POLICY "Users can insert their own learning events" ON learning_events
    FOR INSERT WITH CHECK (student_id::uuid = auth.uid());

CREATE POLICY "Users can select their own learning events" ON learning_events
    FOR SELECT USING (student_id::uuid = auth.uid());

-- Create policies for student_mastery
CREATE POLICY "Users can insert their own mastery" ON student_mastery
    FOR INSERT WITH CHECK (student_id::uuid = auth.uid());

CREATE POLICY "Users can select their own mastery" ON student_mastery
    FOR SELECT USING (student_id::uuid = auth.uid());

CREATE POLICY "Users can update their own mastery" ON student_mastery
    FOR UPDATE USING (student_id::uuid = auth.uid()) WITH CHECK (student_id::uuid = auth.uid());
