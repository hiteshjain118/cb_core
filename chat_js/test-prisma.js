#!/usr/bin/env node

/**
 * Simple test script to verify Prisma setup
 * Run with: node test-prisma.js
 */

async function testPrisma() {
  try {
    console.log('Testing Prisma setup...');
    
    // Test dynamic import
    const { PrismaClient } = await import('@prisma/client');
    console.log('✅ Prisma client imported successfully');
    
    // Test client creation
    const prisma = new PrismaClient();
    console.log('✅ Prisma client created successfully');
    
    // Test connection (this will fail if DATABASE_URL is not set)
    try {
      await prisma.$connect();
      console.log('✅ Database connection successful');
      
      // Test a simple query
      const result = await prisma.$queryRaw`SELECT 1 as test`;
      console.log('✅ Database query successful:', result);
      
      await prisma.$disconnect();
      console.log('✅ Database connection closed');
    } catch (dbError) {
      console.log('⚠️  Database connection failed (expected if DATABASE_URL not set):', dbError.message);
    }
    
    console.log('\n🎉 Prisma setup test completed successfully!');
    
  } catch (error) {
    console.error('❌ Prisma setup test failed:', error.message);
    console.log('\nTo fix this:');
    console.log('1. Run: npm install prisma @prisma/client');
    console.log('2. Run: npx prisma generate');
    console.log('3. Set DATABASE_URL in your .env file');
    console.log('4. Run: npx prisma db push');
  }
}

testPrisma(); 