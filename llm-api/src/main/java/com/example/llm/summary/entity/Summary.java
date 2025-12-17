package com.example.llm.summary.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "context_summary", uniqueConstraints = {
    @UniqueConstraint(name = "uk_callkey", columnNames = "callkey")
})
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Summary {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "callkey", nullable = false, unique = true, length = 100)
    private String callkey;
    
    @Column(name = "original_text", nullable = false, columnDefinition = "TEXT")
    private String originalText;
    
    @Column(name = "summarized_text", columnDefinition = "TEXT")
    private String processedText;  // LLM 처리 결과 (요약, 번역, 분석 등)
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    public void updateProcessedText(String processedText) {
        this.processedText = processedText;
    }
}

