<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
   exclude-result-prefixes="xd"
   version="1.0">
   <xd:doc scope="stylesheet">
      <xd:desc>
         <xd:p><xd:b>Created on:</xd:b> Jan 16, 2011</xd:p>
         <xd:p><xd:b>Author:</xd:b> peterbinkley</xd:p>
         <xd:p></xd:p>
      </xd:desc>
   </xd:doc>
   <xsl:output method="html" encoding="utf-8"/>
   <!-- timestamp_fetch="2011-01-17 08:45:44-0700" -->
   <xsl:variable name="ts" select="substring(translate(/tweetarchive/statuses[@list='user_timeline']/@timestamp_fetch, ' :', '-'), 1, 17)"/>
   <xsl:key name="status-by-month" match="status | direct_message" use="substring(@timestamp, 1, 7)"/>
   <xsl:key name="status-by-id" match="status | direct_message" use="id"/>
   <xsl:template match="/">
      <html>
         <head>
            <title>tweets</title>
         </head>
         <style type="text/css">
            .status {
               margin-top: 1em;
            }
            .reply {
               margin-left: 4em;
            }
            .other {
               margin-top: 1em;
               margin-left: 2em;
               background-color: #ccc;
            }
            .message {
         border: 1px solid red;
         }</style>
         <body>
            <h1>Tweets <xsl:value-of select="$ts"/></h1>
            
            
            <xsl:for-each select="/tweetarchive/statuses/*[count(key('status-by-month', substring(@timestamp, 1, 7))[1] | .) = 1]">
               <xsl:sort select="@timestamp"/>
               <h2><xsl:value-of select="substring(@timestamp, 1, 7)"/></h2>
               <xsl:apply-templates select="key('status-by-month', substring(@timestamp, 1, 7))[count(. | key('status-by-id', id)[1]) = 1]">
                  <xsl:sort select="@timestamp" data-type="text"/>
               </xsl:apply-templates>
            </xsl:for-each>
            
            
         </body>
      </html>
   </xsl:template>
   
   <xsl:template match="status | direct_message">
      <div>
         <xsl:attribute name="class">
            <xsl:choose>
               <xsl:when test="(user/screen_name = 'pabinkley' or sender/screen_name = 'pabinkley') and in_reply_to_status_id != ''">status reply</xsl:when>
               <xsl:when test="user/screen_name = 'pabinkley' or sender/screen_name = 'pabinkley'">status</xsl:when>
               <xsl:otherwise>other</xsl:otherwise>
            </xsl:choose>
            <xsl:if test="name() = 'direct_message'"> message</xsl:if>
         </xsl:attribute>
         <xsl:value-of select="position()"/>
         <xsl:text>. </xsl:text>
         <xsl:value-of select="text"/>
         <br/>
         <xsl:apply-templates select="user | sender"/>
         <xsl:apply-templates select="recipient" mode="inline"/>
         <xsl:value-of select="created_at"/>
         <xsl:value-of select="id"/>
         <xsl:apply-templates select="in_reply_to_status_id"/>
      </div>
   </xsl:template>
   
   <xsl:template match="in_reply_to_status_id">
      <xsl:text> - reply to </xsl:text>
      <xsl:value-of select="in_reply_to_status_id"/>
   </xsl:template>
   
   <xsl:template match="user | sender | recipient">
      <xsl:value-of select="screen_name"/>
      <xsl:text> (</xsl:text>
      <xsl:value-of select="name"/>
      <xsl:text>) </xsl:text>
   </xsl:template>
   
   <xsl:template match="recipient" mode="inline">
      <xsl:text> to </xsl:text>
      <xsl:apply-templates select="."/>
   </xsl:template>
</xsl:stylesheet>