<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-white drop-shadow-lg">👤 角色管理</h1>
      <p class="text-lg text-white/90 drop-shadow">自定义角色外观与行为</p>
    </div>

    <div class="glass-card p-6 max-w-4xl mx-auto">
      <el-form label-position="top">
        <el-form-item label="角色名称">
          <el-input v-model="character.name" placeholder="输入角色名称" />
        </el-form-item>
        <el-form-item label="角色描述">
          <el-input v-model="character.description" type="textarea" rows="3" placeholder="输入角色描述" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveCharacter">保存</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const character = reactive({
  name: '',
  description: ''
})

const saveCharacter = () => {
  console.log('Saving character:', character)
}
</script>
