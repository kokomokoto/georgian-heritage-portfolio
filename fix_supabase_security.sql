-- Enable RLS on user_visits table
ALTER TABLE user_visits ENABLE ROW LEVEL SECURITY;

-- Allow anonymous inserts for tracking (anyone can track visits)
CREATE POLICY "Allow anonymous inserts for tracking" ON user_visits
FOR INSERT WITH CHECK (true);

-- Service role can read all data (for analytics dashboard only)
CREATE POLICY "Service role can read all visits" ON user_visits
FOR SELECT USING (auth.jwt() ->> 'role' = 'service_role');

-- Service role can delete old data
CREATE POLICY "Service role can delete old visits" ON user_visits
FOR DELETE USING (auth.jwt() ->> 'role' = 'service_role');

-- NO policies for regular users to read their own data
-- This ensures users cannot see any analytics data, even their own