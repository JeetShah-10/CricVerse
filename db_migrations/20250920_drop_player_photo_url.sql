-- Migration: Drop player.photo_url column if it exists; ensure image_url exists
-- Safe to run multiple times
DO $$
BEGIN
    -- Ensure image_url exists before dropping photo_url
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'player' AND column_name = 'image_url'
    ) THEN
        ALTER TABLE player ADD COLUMN image_url VARCHAR(200);
    END IF;

    -- Drop photo_url if present
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'player' AND column_name = 'photo_url'
    ) THEN
        ALTER TABLE player DROP COLUMN photo_url;
    END IF;
END $$;
