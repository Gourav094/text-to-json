const express = require('express');
const app = express();

const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get("/profiles", async (req, res) => {
    const {text} = req.body;

    const response = await fetch("http://localhost:8000/llm/extract/profiles", {
        method: "POST",
        headers: {"Content-Type" : "application/json"},
        body: JSON.stringify({text})
    })

    try{
        const body = await response.json();
        res.json({body});
    }
    catch{
        console.log("Error from LLM service in generating json")
    }
})

app.get("/", (req, res) => {
    res.json("Welcome to JSON extractor applicaiton!");
})

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`)
})