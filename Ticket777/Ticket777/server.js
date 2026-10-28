var express = require("express");
var path = require("path");

var app = express();
var port = 8080;

app.use(express.static(path.join(__dirname, 'public')));

app.get(/.*/, function(req, res){
    res.sendFile(path.join(__dirname, 'public', 'ticket.html'));
})

app.listen(port, function(){
    console.log("Server is running on port " + port);
})