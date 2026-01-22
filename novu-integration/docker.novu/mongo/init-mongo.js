// MongoDB initialization script for Novu
// This script creates the necessary database and user for Novu

db = db.getSiblingDB('novu-db');

// Create indexes for better performance
db.notifications.createIndex({ "subscriberId": 1, "createdAt": -1 });
db.notifications.createIndex({ "subscriberId": 1, "read": 1 });
db.notifications.createIndex({ "subscriberId": 1, "seen": 1 });
db.notifications.createIndex({ "_environmentId": 1, "createdAt": -1 });

db.messages.createIndex({ "_subscriberId": 1, "createdAt": -1 });
db.messages.createIndex({ "_environmentId": 1, "createdAt": -1 });

db.subscribers.createIndex({ "subscriberId": 1, "_environmentId": 1 }, { unique: true });
db.subscribers.createIndex({ "_environmentId": 1 });

db.jobs.createIndex({ "status": 1, "createdAt": -1 });
db.jobs.createIndex({ "_subscriberId": 1, "status": 1 });

print('Novu MongoDB initialization completed successfully!');
