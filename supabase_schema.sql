-- Supabase SQL Schema for User Monitoring
-- Run this in your Supabase SQL Editor

-- Create user_visits table
CREATE TABLE IF NOT EXISTS user_visits (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    page_url TEXT,
    screen_resolution TEXT,
    referrer TEXT,
    user_id INTEGER, -- References your app's user ID if authenticated
    action TEXT DEFAULT 'page_view', -- page_view, project_click, etc.
    project_id TEXT, -- For tracking specific project interactions
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_visits_session_id ON user_visits(session_id);
CREATE INDEX IF NOT EXISTS idx_user_visits_timestamp ON user_visits(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_visits_ip_address ON user_visits(ip_address);
CREATE INDEX IF NOT EXISTS idx_user_visits_user_id ON user_visits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_visits_action ON user_visits(action);

-- Enable Row Level Security (RLS)
ALTER TABLE user_visits ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserts (for tracking visits)
CREATE POLICY "Allow anonymous inserts" ON user_visits
    FOR INSERT
    WITH CHECK (true);

-- Create policy to allow authenticated users to read their own data
CREATE POLICY "Users can read their own visits" ON user_visits
    FOR SELECT
    USING (auth.uid()::text = user_id::text);

-- Create policy for admin/service role to read all data
CREATE POLICY "Service role can read all visits" ON user_visits
    FOR SELECT
    USING (auth.role() = 'service_role');

-- Optional: Create a view for analytics
CREATE OR REPLACE VIEW user_analytics AS
SELECT
    DATE(timestamp) as date,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(*) as total_visits,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT CASE WHEN user_id IS NOT NULL THEN user_id END) as authenticated_users,
    array_agg(DISTINCT screen_resolution) FILTER (WHERE screen_resolution IS NOT NULL) as screen_resolutions,
    array_agg(DISTINCT action) FILTER (WHERE action IS NOT NULL) as actions
FROM user_visits
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Grant permissions
GRANT SELECT ON user_analytics TO authenticated;
GRANT SELECT ON user_analytics TO service_role;