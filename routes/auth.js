import express from 'express'
import bcrypt from 'bcryptjs'
import User from '../models/user.js'
import jwt from "jsonwebtoken"

const router = express.Router()

// routes/auth.js
router.post('/signup', async (req, res) => {
    const { name, email, password, confirmPassword } = req.body
  
    if (password !== confirmPassword) {
      return res.status(400).json({ message: "Password mismatch confirmation Password" })
    }
  
    try {
      const existingUser = await User.findOne({ email })
      if (existingUser) return res.status(400).json({ msg: 'User already exists' })
  
      const hashedPassword = await bcrypt.hash(password, 10)
      const token = jwt.sign({ id: email }, "mohamed")
      const newUser = new User({ name, email, password: hashedPassword }) // ✅ Don't save confirmPassword
      await newUser.save()
      res.status(201).json({ msg: 'User created successfully', token})
    } catch (err) {
      res.status(500).json({ msg: 'Server error' })
    }
  })
  
// Login
router.post('/login', async (req, res) => {
  const { email, password } = req.body
  try {
    const user = await User.findOne({ email })
    if (!user) return res.status(400).json({ msg: 'Invalid credentials' })
    const token = jwt.sign({ id: email }, "mohamed")
    const isMatch = await bcrypt.compare(password, user.password)
    if (!isMatch) return res.status(400).json({ msg: 'Invalid credentials' })

    res.json({ msg: 'Login successful', user })
  } catch (err) {
    res.status(500).json({ msg: 'Server error' })
  }
})

export default router
