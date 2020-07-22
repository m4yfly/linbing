<style lang="less">
  @import './shownote.less';
</style>

<template>
  <div>
    <Card class="card">
            <p slot="title">
                <Icon type="ios-book"></Icon>
                <span>{{item.notename}}</span>
                <span class = "time">{{item.time}}</span>
            </p>
            <mavon-editor ref=md v-model="item.content"   @keydown=""  :subfield="false" defaultOpen="preview" :toolbarsFlag="false" :editable="false" :scrollStyle="true" class="editor"/>
            <p>
              <Button  type="info"  @click="trash(item)" size="small" class="button">
                              删除
              </Button>
              <Button  type="info"  @click="edit(item)" size="small" class="button">
                              编辑
              </Button>
            </p>
    </Card>
  </div>
</template>

<script>
import RSA  from '@/libs/crypto'
import http  from '@/libs/http'
import {getToken } from '@/libs/util'
import MarkdownItVue from 'markdown-it-vue'
export default {
  inject: ['reload'],
  components: {
    MarkdownItVue
  },
  data () {
    return {
      item: {},
      token: getToken(),
      username: '',
    }
  },
  created () {
    this.$nextTick(this.getParams())
  },
  methods: {
    getParams () {
      this.item = JSON.parse(JSON.stringify(this.$route.query.params))
    },
    edit (params) {
      this.$router.push({
        name:'修改笔记',
        query:{
          params : this.item
        }
      })
    },
    trash (item) {
        let data = {
            'notename': item.notename,
            'flag': '1',
            'token': this.token.trim()
        }
        data = JSON.stringify(data)
        let req_params = {'data': RSA.Encrypt(data)}
        http.post('/api/setflag', req_params).then((res) => {
            res.data = eval('(' + res.data + ')')
            switch(res.data.code ){
            case'Z1000':
            setTimeout(() => {
                    this.$router.push({
                    path: '/components/notelist'
                    })
                },3000)
            break
            case 'Z1001':
            this.$Notice.error({
                title: '请求失败',
                desc: '系统发生异常,请稍后再次尝试'
            })
            break
            case 'Z1002':
            this.$Notice.error({
                title: '请求失败',
                desc: '系统发生异常,请稍后再次尝试'
            })
            break
            case 'Z1004':
            this.$Notice.error({
                title: '请求失败',
                desc: '认证失败,请稍后再次尝试'
            })
            break
            default:
            break
            }
        })
      }
    }
}
</script>

