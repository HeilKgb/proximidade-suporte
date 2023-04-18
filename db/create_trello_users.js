use risk3

db.trello_users.remove();

// Add Depara Users Trello x Risk3
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de5997"), "email" : "marcos@risk3.com.br", "fullName" : "Marcos de Almeida Leone Filho", "idMember" : "509aa706c3f9df790a008465", "username" : "marcosleonefilho" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de5998"), "email" : "makoto@risk3.com.br", "fullName" : "Makoto Kadowaki", "idMember" : "509c10674d0954886500340f", "username" : "makotokadowaki" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de5999"), "email" : "makray@risk3.com.br", "fullName" : "João Makray", "idMember" : "504639cf5dee1f0876779014", "username" : "joaomak" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de599a"), "email" : "joao@risk3.com.br", "fullName" : "João Borsoi Soares", "idMember" : "509b94fd52a7c36c38026a34", "username" : "joaoborsoisoares" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de599b"), "email" : "ana@risk3.com.br", "fullName" : "Ana Paula Diniz Marques", "idMember" : "5ef644dc687fbe7d9c86d6ba", "username" : "anapauladinizm" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de599c"), "email" : "rafael@risk3.com.br", "fullName" : "Rafael Giordano Vieira", "idMember" : "56f45789996395c0514c5fbf", "username" : "rafaelgiordano1" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de599d"), "email" : "carlos@risk3.com.br", "fullName" : "Carlos Costa", "idMember" : "6048cd83cdac5b74b003acfc", "username" : "carloscosta265" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de599e"), "email" : "paulo@risk3.com.br", "fullName" : "Paulo Mayon", "idMember" : "5effb9a4752bfd21155e0c20", "username" : "paulomayon1" });
db.trello_users.insert({ "_id" : ObjectId("61885aab9be58354b8de599f"), "email" : "andre@risk3.com.br", "fullName" : "André Mayon", "idMember" : "6099474e10f6cd38d018e520", "username" : "andremayon2" });
db.trello_users.insert({ "_id" : ObjectId("6194168a50f80feefb76c089"), "email" : "suporte@risk3.com.br", "fullName" : "Suporte Risk3", "idMember" : "619411e6537b6e4adcb215dc", "username" : "suportevenidera" });
db.trello_users.insert({ "_id" : ObjectId("6225facf5b51468fa4fff2ad"), "email": "mirela@risk3.com.br", "fullName": "Mirela Rezende Silva", "idMember": "6213e6e19b5c3481ce639de7", "username": "mirelarezendesilva" });
// Create a index
db.trello_users.createIndex({"email": 1}, {unique: true});