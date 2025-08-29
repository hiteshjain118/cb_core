#!/bin/bash

echo "Setting up Prisma for chat_js project..."

# Install Prisma dependencies
echo "Installing Prisma dependencies..."
npm install prisma @prisma/client

# Generate Prisma client
echo "Generating Prisma client..."
npx prisma generate

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Database connection for Supabase PostgreSQL
DATABASE_URL="postgresql://username:password@host:port/database?schema=public"

# Example for Supabase:
# DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
EOF
    echo "Created .env file. Please update it with your actual database credentials."
else
    echo ".env file already exists."
fi

# Test the setup
echo ""
echo "Testing Prisma setup..."
if node test-prisma.js; then
    echo "✅ Prisma setup test passed!"
else
    echo "⚠️  Prisma setup test had issues (this is normal if DATABASE_URL is not set)"
fi

echo ""
echo "Prisma setup complete!"
echo ""
echo "Next steps:"
echo "1. Update the .env file with your actual DATABASE_URL"
echo "2. Run 'npx prisma db push' to push the schema to your database"
echo "3. Or run 'npx prisma migrate dev --name init' for production migrations"
echo "4. Test with: node test-prisma.js"
echo ""
echo "You can now use the Prisma client in your TypeScript code!" 