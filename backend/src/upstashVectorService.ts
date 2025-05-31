import { Index } from '@upstash/vector';
import dotenv from 'dotenv';

dotenv.config();

async function testUpstashVectorConnection() {
  try {
    if (!process.env.UPSTASH_VECTOR_REST_URL || !process.env.UPSTASH_VECTOR_REST_TOKEN) {
      throw new Error('Upstash Vector URL or Token not configured');
    }

    const index = new Index({
      url: process.env.UPSTASH_VECTOR_REST_URL,
      token: process.env.UPSTASH_VECTOR_REST_TOKEN,
    });

    console.log('Successfully initialized Upstash Vector client.');
    const vectorId = 'test-vector-1';
    const vectorData = [0.1, 0.2, 0.3];

    await index.upsert([
      {
        id: vectorId,
        vector: vectorData,
        metadata: { test: 'data' },
      },
    ]);
    console.log(`Upserted test vector with id: ${vectorId}`);

    const results = await index.query({
      vector: vectorData,
      topK: 1,
      includeVectors: true,
      includeMetadata: true,
    });
    console.log('Query results:', results);

    if (results && results.length > 0 && results[0].id === vectorId) {
      console.log('Upstash Vector connection and basic operations successful!');
    } else {
      console.warn('Could not verify data with query or no results found.');
    }
    console.log(`Deleted test vector with id: ${vectorId}`);


  } catch (error) {
    console.error('Failed to connect to Upstash Vector or perform operation:', error);
  }
}

// 実行例
// testUpstashVectorConnection();